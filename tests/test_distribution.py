"""Exercise generated distribution drift and isolated skill resources."""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def test_native_validator_is_read_only_without_persistent_memory(self):
        validator = (ROOT / "agents/spec-design-validator.md").read_text()
        frontmatter = validator.split("---", 2)[1]
        self.assertNotRegex(frontmatter, r"(?m)^memory:")
        self.assertIn("Leave the working tree, index, and commit history exactly as you found them", validator)
        for instruction in ("Update your agent memory", "Use the Write and Edit tools",
                            "Persistent Agent Memory", "agent-memory/spec-design-validator"):
            with self.subTest(instruction=instruction):
                self.assertNotIn(instruction, validator)

    def test_committed_distribution_is_current(self):
        subprocess.run([sys.executable, str(ROOT / "scripts/build-distribution.py"), "--check"], check=True)

    def test_drift_is_detected_and_repaired(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for directory in ("scripts", "skills", "adapters", "agents"):
                shutil.copytree(ROOT / directory, root / directory)
            target = root / "agents/spec-design-validator.md"
            target.write_text("stale\n")
            command = [sys.executable, str(root / "scripts/build-distribution.py")]
            self.assertNotEqual(subprocess.run(command + ["--check"], capture_output=True).returncode, 0)
            subprocess.run(command, check=True, capture_output=True)
            subprocess.run(command + ["--check"], check=True, capture_output=True)
            self.assertEqual(target.read_bytes(), (ROOT / "agents/spec-design-validator.md").read_bytes())

    def test_independent_skill_resources(self):
        required = {
            "agentic-loop": ["references/dispatch.md", "references/roles/code-reviewer.md", "references/roles/team-lead.md", "references/validation/workflow.md", "references/validation/references/validator-role.md", "references/validation/references/report-format.md", "references/validation/prompts/validator-instance.md", "scripts/check-gates.sh", "setup/hooks/lib-gates.sh", "scripts/init-run.sh"],
            "validating-specs": ["references/dispatch.md", "references/validator-role.md", "references/report-format.md", "prompts/validator-instance.md"],
            "writing-documentation": ["references/dispatch.md"],
        }
        for skill, resources in required.items():
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as tmp:
                root = pathlib.Path(tmp) / skill
                shutil.copytree(ROOT / "skills" / skill, root)
                for resource in resources:
                    self.assertTrue((root / resource).is_file(), resource)
                self.assertEqual(list(root.rglob("SKILL.md")), [root / "SKILL.md"])


if __name__ == "__main__":
    unittest.main()
