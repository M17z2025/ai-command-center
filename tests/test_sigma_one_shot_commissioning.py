import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sigma_runtime.store import MissionStore


class OneShotCommissioningTests(unittest.TestCase):
    def test_marks_old_running_missions_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MissionStore(Path(tmp) / "runtime.db")
            store.create_mission("old", "prompt", "runner", {})
            old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
            with store._connect() as conn:
                conn.execute(
                    "UPDATE missions SET updated_at=? WHERE id=?",
                    (old, "old"),
                )
            stale = store.mark_stale_running(older_than_seconds=1800)
            self.assertEqual(stale, ["old"])
            mission = store.get_mission("old")
            self.assertEqual(mission["status"], "STALE")
            self.assertIn(
                "stale-detected",
                [event["stage"] for event in mission["events"]],
            )

    def test_does_not_mark_fresh_running_mission_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MissionStore(Path(tmp) / "runtime.db")
            store.create_mission("fresh", "prompt", "runner", {})
            stale = store.mark_stale_running(older_than_seconds=1800)
            self.assertEqual(stale, [])
            self.assertEqual(store.get_mission("fresh")["status"], "RUNNING")

    def test_one_shot_scripts_are_present(self):
        root = Path(__file__).resolve().parents[1]
        shell = (root / "scripts" / "sigma_one_shot_commission.sh").read_text()
        python = (root / "scripts" / "sigma_one_shot_commission.py").read_text()
        self.assertIn("SIGMA_ONE_SHOT_COMMISSIONING_PASS", shell)
        self.assertIn("PRE_RESTART_PASS", python)
        self.assertIn('"status": "PASS"', python)
        self.assertIn("restart sigma-memory sigma-runtime", shell)
        self.assertIn("stop sigma-runner", shell)


if __name__ == "__main__":
    unittest.main()
