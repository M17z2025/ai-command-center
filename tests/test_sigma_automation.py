"""Independent acceptance tests for durable intake and deterministic authority gates."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import yaml

from sigma_runtime.automation import IntakeError, QueueStore, intake, project_policy
from sigma_runtime.automation_worker import GuardedGateway, ProjectRunner
from sigma_runtime.portfolio_runner import RepositorySnapshot, WorkItem


class AutomationCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = QueueStore(self.root / 'queue.db')
        self.repo = 'owner/project'
        self.policies = {self.repo: {'enabled': True, 'execute': True, 'interval_seconds': 300}}
        self.secret = 'test-only-secret-' * 3

    def headers(self, body, delivery='11111111-1111-1111-1111-111111111111', event='issues'):
        return {'X-Hub-Signature-256': 'sha256=' + hmac.new(self.secret.encode(), body, hashlib.sha256).hexdigest(),
                'X-GitHub-Delivery': delivery, 'X-GitHub-Event': event}

    def body(self, repo=None, **extra):
        return json.dumps({'action': 'opened', 'repository': {'full_name': repo or self.repo}, **extra}).encode()

    def row(self, job_id):
        with self.store.connect() as db:
            return dict(db.execute('SELECT * FROM automation_jobs WHERE id=?', (job_id,)).fetchone())

    def write_policy(self):
        (self.root / 'projects').mkdir(exist_ok=True)
        (self.root / 'projects/registry.yaml').write_text(yaml.safe_dump({'projects': [
            {'repository': self.repo, 'name': 'Project', 'lifecycle': 'active', 'category': 'software'}]}))
        (self.root / 'projects/automation.yaml').write_text(yaml.safe_dump({'projects': self.policies}))


class IntakeTests(AutomationCase):
    def test_valid_signed_delivery_and_replay_after_completion(self):
        body = self.body(issue={'body': 'private instruction', 'authority': 'root'})
        self.assertEqual(intake(self.store, self.policies, self.secret, body, self.headers(body)), 'accepted')
        job = self.store.claim()
        self.store.finish(job['id'], job['claim'], 'DONE', {})
        restarted = QueueStore(self.store.path)
        self.assertEqual(intake(restarted, self.policies, self.secret, body, self.headers(body)), 'duplicate')
        self.assertIsNone(restarted.claim())
        self.assertNotIn('private instruction', json.dumps(restarted.status()))

    def test_invalid_signature_changed_body_or_missing_secret_does_not_enqueue(self):
        body = self.body()
        for secret, content, headers in [(self.secret, body, {}),
                                          (self.secret, body + b' ', self.headers(body)),
                                          ('', body, self.headers(body))]:
            with self.subTest(secret_present=bool(secret), content=content):
                with self.assertRaises(IntakeError):
                    intake(self.store, self.policies, secret, content, headers)
        self.assertIsNone(self.store.claim())

    def test_cross_repository_and_oversized_body_are_rejected(self):
        for body in [self.body('attacker/project'), b'x' * 262145]:
            with self.assertRaises(IntakeError):
                intake(self.store, self.policies, self.secret, body, self.headers(body))
        self.assertIsNone(self.store.claim())

    def test_delivery_identity_cannot_be_reused_with_different_body(self):
        first, second = self.body(), self.body(action='edited')
        intake(self.store, self.policies, self.secret, first, self.headers(first))
        with self.assertRaises(IntakeError):
            intake(self.store, self.policies, self.secret, second, self.headers(second))
        self.assertEqual(self.store.status()['counts'], {'QUEUED': 1})

    def test_invalid_json_unknown_event_and_invalid_delivery(self):
        bad = b'not-json'
        with self.assertRaises(ValueError):
            intake(self.store, self.policies, self.secret, bad, self.headers(bad))
        body = self.body()
        self.assertEqual(intake(self.store, self.policies, self.secret, body, self.headers(body, event='issue_comment')), 'ignored')
        with self.assertRaises(IntakeError):
            intake(self.store, self.policies, self.secret, body, self.headers(body, delivery='short'))
        self.assertIsNone(self.store.claim())


class QueueTests(AutomationCase):
    def test_concurrent_claim_and_per_repository_coalescing(self):
        with ThreadPoolExecutor(max_workers=8) as executor:
            ids = list(executor.map(lambda _: self.store.enqueue(self.repo, now=1), range(16)))
        self.assertEqual(len(set(ids)), 1)
        self.store.enqueue('owner/other', now=2)
        with ThreadPoolExecutor(max_workers=8) as executor:
            claimed = list(executor.map(lambda _: self.store.claim(now=10), range(16)))
        self.assertEqual(len([c for c in claimed if c]), 1)
        self.assertEqual(self.store.status()['counts'], {'QUEUED': 1, 'RUNNING': 1})

    def test_restart_preserves_pending_identity_and_attempts(self):
        ident = self.store.enqueue(self.repo, now=1)
        restarted = QueueStore(self.store.path)
        job = restarted.claim(now=2)
        self.assertEqual(job['id'], ident)
        restarted.fail(ident, job['claim'], 'Transient', now=3)
        self.assertEqual(QueueStore(self.store.path).status()['recent'][0]['attempt'], 1)
        self.assertIsNone(restarted.claim(now=62))
        self.assertEqual(restarted.claim(now=63)['attempt'], 2)

    def test_retry_backoff_exhaustion_holds_without_hot_loop(self):
        ident = self.store.enqueue(self.repo, now=0)
        due = 0
        for attempt, delay in [(1, 60), (2, 120), (3, 240)]:
            job = self.store.claim(now=due)
            self.assertEqual(job['attempt'], attempt)
            self.store.fail(ident, job['claim'], 'Transient', now=due)
            self.assertIsNone(self.store.claim(now=due + delay - 1))
            due += delay
        self.assertEqual(self.row(ident)['state'], 'DEAD')
        self.assertIsNone(self.store.enqueue(self.repo, now=due))
        self.assertEqual(self.store.status()['holds'][0]['job_id'], ident)

    def test_ambiguous_dispatch_quarantines_and_fences_old_claim(self):
        ident = self.store.enqueue(self.repo, now=0)
        job = self.store.claim(now=1)
        self.store.dispatching(ident, job['claim'])
        self.store.fail(ident, job['claim'], 'Timeout', now=2)
        self.assertEqual(self.row(ident)['state'], 'UNKNOWN')
        self.assertIsNone(self.store.enqueue(self.repo, now=10000))
        self.assertFalse(self.store.finish(ident, job['claim'], 'DONE', {}))
        with self.assertRaises(IntakeError):
            self.store.dispatching(ident, job['claim'])

    def test_stale_recovery_and_fencing(self):
        ident = self.store.enqueue(self.repo, now=0)
        old = self.store.claim(now=1)
        self.store.recover(now=120, stale_seconds=120)
        self.assertEqual(self.row(ident)['state'], 'RUNNING')
        self.store.recover(now=122, stale_seconds=120)
        new = self.store.claim(now=182)
        self.assertNotEqual(old['claim'], new['claim'])
        self.assertFalse(self.store.heartbeat(ident, old['claim'], now=190))
        self.assertFalse(self.store.finish(ident, old['claim'], 'DONE', {}))
        self.assertTrue(self.store.finish(ident, new['claim'], 'DONE', {}))

    def test_heartbeat_prevents_recovery_and_dispatched_stale_holds(self):
        ident = self.store.enqueue(self.repo, now=0)
        job = self.store.claim(now=1)
        self.store.heartbeat(ident, job['claim'], now=110)
        self.store.recover(now=122, stale_seconds=120)
        self.assertEqual(self.row(ident)['state'], 'RUNNING')
        self.store.dispatching(ident, job['claim'])
        self.store.recover(now=231, stale_seconds=120)
        self.assertEqual(self.row(ident)['state'], 'UNKNOWN')
        self.assertIsNone(self.store.enqueue(self.repo, now=232))

    def test_schedule_fairness_durable_slots_and_missed_slot_coalescing(self):
        policies = {self.repo: {'interval_seconds': 300}, 'owner/other': {'interval_seconds': 600}}
        self.store.schedule(policies, now=0)
        seen = set()
        for _ in range(2):
            job = self.store.claim(now=0)
            seen.add(job['repository'])
            self.store.finish(job['id'], job['claim'], 'DONE', {})
        self.assertEqual(seen, set(policies))
        restarted = QueueStore(self.store.path)
        restarted.schedule(policies, now=299)
        self.assertIsNone(restarted.claim(now=299))
        restarted.schedule(policies, now=300)
        self.assertEqual(restarted.claim(now=300)['repository'], self.repo)
        restarted.schedule(policies, now=100000)
        self.assertEqual(restarted.status()['counts']['QUEUED'], 1)
        self.assertEqual(restarted.status()['counts']['RUNNING'], 1)

    def test_policy_requires_registered_active_explicit_enablement(self):
        self.write_policy()
        self.assertIn(self.repo, project_policy(self.root))
        self.policies[self.repo]['enabled'] = False
        self.write_policy()
        self.assertEqual(project_policy(self.root), {})
        self.policies['attacker/repo'] = {'enabled': True}
        self.write_policy()
        with self.assertRaises(IntakeError):
            project_policy(self.root)


class GatewayTests(AutomationCase):
    def setUp(self):
        super().setUp()
        self.write_policy()
        self.store.enqueue(self.repo, now=1)
        self.job = self.store.claim(now=2)
        self.delegate = Mock()
        self.delegate.dispatch.return_value = {'status': 'TESTED'}
        self.github = Mock(allow_write=True, token='test-token')
        self.github.repository.return_value = {'default_branch': 'main'}
        self.github.latest_commit.return_value = {'sha': 'a' * 40}
        self.manifest = {'project': {'repository': self.repo}, 'automation': {
            'enabled': True, 'execution': 'branch_pr', 'owner_gates': 'preserve'}}
        self.github.file_text.side_effect = lambda repo, name, head: yaml.safe_dump(self.manifest) if name == '.sigma/project.yaml' else 'trusted contract'
        self.issue = {'state': 'open', 'title': 'Fix thing', 'body': 'Scope', 'labels': [{'name': 'sigma:autonomous'}]}
        self.github.request.return_value = self.issue
        self.github.open_pulls.return_value = []
        self.payload = {'repository': self.repo, 'issue_number': 1, 'objective': 'Fix thing', 'issue_body': 'Scope', 'authority': {'production_release': True}}
        self.gateway = GuardedGateway(self.delegate, self.github, self.store, self.job, self.root)
        env = patch.dict(os.environ, {'SIGMA_RUNNER_EXECUTE': '1'})
        env.start()
        self.addCleanup(env.stop)

    def test_authorized_dispatch_records_intent_provenance_and_denies_escalation(self):
        self.assertEqual(self.gateway.dispatch(self.payload), {'status': 'TESTED'})
        self.assertEqual(self.row(self.job['id'])['dispatch_started'], 1)
        self.assertEqual(self.payload['automation_job_id'], self.job['id'])
        self.assertEqual(self.payload['source_sha'], 'a' * 40)
        self.assertFalse(any(self.payload['authority'].values()))
        for call in self.github.file_text.call_args_list:
            self.assertEqual(call.args[2], 'a' * 40)

    def assert_blocked(self):
        with self.assertRaises(IntakeError):
            self.gateway.dispatch(self.payload)
        self.delegate.dispatch.assert_not_called()
        self.assertEqual(self.row(self.job['id'])['dispatch_started'], 0)

    def test_cross_project_dispatch_rejected(self):
        self.payload['repository'] = 'owner/other'
        self.assert_blocked()

    def test_disabled_project_rechecked_at_dispatch(self):
        self.policies[self.repo]['execute'] = False
        self.write_policy()
        self.assert_blocked()

    def test_global_execution_and_write_authority_required(self):
        with patch.dict(os.environ, {'SIGMA_RUNNER_EXECUTE': '0'}):
            self.assert_blocked()
        self.github.allow_write = False
        self.assert_blocked()
        self.github.allow_write = True
        self.github.token = None
        self.assert_blocked()

    def test_product_contract_cannot_opt_out_of_owner_gates(self):
        self.manifest['automation']['owner_gates'] = 'bypass'
        self.assert_blocked()

    def test_product_contract_explicit_opt_in_and_repository_identity_required(self):
        self.manifest['automation']['enabled'] = False
        self.assert_blocked()
        self.manifest['automation']['enabled'] = True
        self.manifest['project']['repository'] = 'owner/other'
        self.assert_blocked()

    def test_issue_changed_closed_or_label_removed_after_planning_rejected(self):
        for field, value in [('state', 'closed'), ('title', 'Different objective'), ('body', 'New scope'), ('labels', [])]:
            original = self.issue[field]
            self.issue[field] = value
            self.assert_blocked()
            self.issue[field] = original

    def test_existing_pr_and_missing_authority_document_block(self):
        self.github.open_pulls.return_value = [{'number': 3}]
        self.assert_blocked()
        self.github.open_pulls.return_value = []
        self.github.file_text.side_effect = lambda repo, name, head: yaml.safe_dump(self.manifest) if name == '.sigma/project.yaml' else None
        self.assert_blocked()

    def test_lost_queue_claim_cannot_dispatch(self):
        self.store.fail(self.job['id'], self.job['claim'], 'StaleWorker', now=5)
        self.assert_blocked()

    def test_selection_filters_unlabelled_work_and_projects_with_prs(self):
        runner = object.__new__(ProjectRunner)
        runner.project_execute = True
        snap = RepositorySnapshot('Project', self.repo, 'active', 'software', accessible=True, manifest_present=True, status_present=True)
        snap.work_items = [WorkItem(self.repo, 1, 'unlabelled', '', 0, (), True),
                           WorkItem(self.repo, 2, 'allowed', '', 1, ('sigma:autonomous',), True)]
        self.assertEqual(runner.select([snap]).issue_number, 2)
        snap.open_prs = 1
        self.assertIsNone(runner.select([snap]))


if __name__ == '__main__':
    unittest.main()

