# Sigma Chat Build Ownership

Every Sigma development chat has an accountable **Build Steward Team**. A chat is a work surface; the linked project repository and its Sigma status are the technical source of truth.

## Operating rule

When a development chat starts or resumes:

1. Resolve the chat to a registered project/repository using explicit repository references first, then exact project names and aliases.
2. Load the project's current repository evidence before making build/status claims.
3. Attach the project's Build Steward Team from `teams.yaml`.
4. Keep the same accountable team across every chat concerning that project.
5. Continue the shared GitHub backlog instead of starting a competing implementation.
6. If no repository can be resolved, attach the Unmapped Build Intake Team and mark the build `PROJECT_REPOSITORY_REQUIRED` until a real repository is registered.
7. Chat closure does not release ownership; responsibility persists until Definition of Done or explicit owner reassignment.

## Core team on every software build

- Accountable continuity: `sigma-chat-build-steward`
- Development plan: `sigma-development-planning-director`
- Engineering: `algorithmic-engineering-director`
- Architecture: `software-architecture-master`
- Coding: `polyglot-coding-master`
- Frontend: `frontend-engineering-master`
- Backend/API: `backend-api-engineering-master`
- Database/data: `database-data-engineering-master`
- Integration/automation: `integration-automation-master`
- CI/tooling: `developer-tooling-ci-master`
- QA/regression: `qa-test-engineering-master`
- Security division: `security-master`
- Independent security verdict: `sigma-security-gatekeeper`
- Real-user acceptance: `sigma-user-tester`
- Open-source/free-component reconnaissance: `sigma-scouter`
- Current evidence/research: `research-director`

Project-specific domain specialists are added in `teams.yaml`.

## Independence

The Build Steward owns continuity, backlog discipline and handoff. The implementer cannot self-certify security or user acceptance. Security Gatekeeper and Sigma User Tester remain independent release gates.

## Blueprint contract

Every project blueprint must carry a **Sigma Build Team & Chat Ownership** section containing:

- canonical project name and repository;
- accountable Build Steward;
- core engineering team;
- domain specialists;
- independent security and user-test gates;
- Sigma Scouter participation;
- rule that all chats for the same product resolve to this same team and repository truth;
- last assignment update date.

The master Drive portfolio blueprint register is the human-readable portfolio index; `teams.yaml` is the machine-readable ownership source.

## Resolver

```bash
python scripts/sigma_chat_owner.py list
python scripts/sigma_chat_owner.py resolve --title "Invoiceit Development Loop"
python scripts/sigma_chat_owner.py resolve --title "Revision section" --message "Humanit GCSE study work"
```

The resolver only uses chat/project information actually supplied or retrieved. It does not claim visibility into a conversation it has not been given.
