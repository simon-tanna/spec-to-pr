import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/agentic-loop/scripts/render-pr-body.sh"


class PrBodyTests(unittest.TestCase):
    def render(self, run_id, metadata=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", tmp], check=True)
            run = root / ".agentic-loop" / run_id
            run.mkdir(parents=True)
            (run / "tasks.json").write_text('{"tasks":[]}')
            if metadata is not None:
                (run / "run-context.json").write_text(json.dumps(metadata))
            return subprocess.check_output(["bash", str(SCRIPT), run_id], cwd=root, text=True)

    def test_file_run_has_no_issue_closure_or_false_authorship(self):
        result = self.render("feature-123abc", {"issue": None})
        self.assertNotIn("Closes #", result)
        self.assertNotIn("Claude", result)
        self.assertIn(".agentic-loop/feature-123abc/spec.md", result)

    def test_issue_run_closes_real_issue(self):
        self.assertIn("Closes #42.", self.render("42", {"issue": "42"}))

    def test_legacy_ci_numeric_run_preserves_closure(self):
        self.assertIn("Closes #42.", self.render("42"))


if __name__ == "__main__":
    unittest.main()
