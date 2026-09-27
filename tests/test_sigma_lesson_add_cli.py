import tempfile
import unittest
from pathlib import Path

from scripts.sigma_mesh_runtime import main
from sigma_runtime.store import MissionStore


class LessonAddCLITests(unittest.TestCase):
    def test_lesson_add_creates_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "runtime.db"
            store = MissionStore(db)
            store.create_mission("m1", "prompt", "test", {})
            rc = main([
                "--db", str(db),
                "lesson-add", "m1",
                "--lesson", "Bound prompts to context windows.",
                "--source", "commissioning-evidence",
            ])
            self.assertEqual(rc, 0)
            lessons = store.list_lessons()
            self.assertEqual(len(lessons), 1)
            self.assertEqual(lessons[0]["status"], "CANDIDATE")
            self.assertEqual(
                lessons[0]["metadata"]["source"],
                "commissioning-evidence",
            )

    def test_lesson_add_requires_existing_mission(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "runtime.db"
            rc = main([
                "--db", str(db),
                "lesson-add", "missing",
                "--lesson", "Example.",
            ])
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
