"""Verify standalone validator generation directly from canonical resources."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("spec-design-validator", "validating-specs", "agentic-loop")


def payload(root, skill):
    """Locate a skill's independently installable native validator resources."""
    return root / "skills" / skill / "references/native-validator"


def rubric(root):
    """Read the canonical review instructions without skill frontmatter."""
    return (root / "skills/spec-design-validator/SKILL.md").read_text().split("\n---\n", 1)[1].strip() + "\n"


class NativeGenerationTests(unittest.TestCase):
    def copy_root(self, destination):
        for directory in ("scripts", "skills", "adapters", "agents"):
            shutil.copytree(ROOT / directory, destination / directory)
        return destination

    def build(self, root, check=False):
        return subprocess.run([sys.executable, str(root / "scripts/build-distribution.py"),
                               *(["--check"] if check else [])], capture_output=True, text=True)

    def test_host_payloads_preserve_rubric_and_worker_contract(self):
        body = rubric(ROOT)
        plugin = (ROOT / "agents/spec-design-validator.md").read_text()
        self.assertEqual(plugin.count(body), 1)
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/skills/spec-design-validator/references/", plugin)
        for skill in SKILLS:
            directory = payload(ROOT, skill)
            self.assertTrue((directory / "claude.md").is_file(), str(directory / "claude.md"))
            claude = (directory / "claude.md").read_text()
            codex = tomllib.loads((directory / "codex.toml").read_text())
            self.assertEqual(set(codex), {"name", "description", "developer_instructions"})
            self.assertEqual(codex["name"], "spec-design-validator")
            self.assertTrue(codex["description"])
            self.assertIn("model: opus\n", claude)
            self.assertIn("disallowedTools: Write, Edit, NotebookEdit, Agent", claude)
            for host in (claude, codex["developer_instructions"]):
                self.assertEqual(host.count(body), 1)
                self.assertIn("The session that dispatched you owns all further dispatch", host)
                self.assertIn("Leave agent memory files unchanged.", host)
                self.assertIn("Leave the working tree, index, and commit history exactly as you found them", host)
                self.assertNotIn("CLAUDE_PLUGIN_ROOT", host)
                self.assertEqual(host.count("{{PROJECT_REFERENCES}}"), 1)
                self.assertIn("read it from `{{PROJECT_REFERENCES}}` instead", host)

    def test_payload_reference_closure_for_each_skill(self):
        references = ROOT / "skills/spec-design-validator/references"
        for skill in SKILLS:
            directory = payload(ROOT, skill)
            self.assertTrue(directory.is_dir(), str(directory))
            self.assertEqual(set(path.name for path in (directory / "references").iterdir()),
                             set(path.name for path in references.iterdir() if path.is_file()))
            for source in references.iterdir():
                if not source.is_file():
                    continue
                text = (directory / "references" / source.name).read_text()
                self.assertTrue(text.endswith(source.read_text()))
            self.assertEqual(list(directory.rglob("SKILL.md")), [])
            for name in ("claude.md", "codex.toml"):
                text = (directory / name).read_text()
                self.assertNotIn(str(ROOT), text)
                self.assertNotIn("../", text)
                self.assertNotIn("skills/validating-specs", text)

    def test_canonical_changes_propagate_without_intermediates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(Path(temporary))
            canonical = root / "skills/spec-design-validator/SKILL.md"
            canonical.write_text(canonical.read_text() + "\nCanonical propagation sentinel.\n")
            reference = root / "skills/spec-design-validator/references/project-checks.md"
            reference.write_text(reference.read_text() + "\nReference propagation sentinel.\n")
            for skill in SKILLS:
                shutil.rmtree(payload(root, skill), ignore_errors=True)
            for path in (root / "skills/validating-specs/references/validator-role.md",
                         root / "skills/validating-specs/references/project-checks.md",
                         root / "agents/spec-design-validator.md"):
                path.unlink()
            result = self.build(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Canonical propagation sentinel.", (root / "agents/spec-design-validator.md").read_text())
            for skill in SKILLS:
                for name in ("claude.md", "codex.toml"):
                    self.assertIn("Canonical propagation sentinel.", (payload(root, skill) / name).read_text())
                self.assertIn("Reference propagation sentinel.",
                              (payload(root, skill) / "references/project-checks.md").read_text())

    def test_native_payload_drift_and_stale_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(Path(temporary))
            directory = payload(root, SKILLS[0])
            self.assertTrue(directory.is_dir(), str(directory))
            changed = directory / "claude.md"
            missing = directory / "codex.toml"
            owned = directory / "references/orphan.md"
            owned_toml = directory / "orphan.toml"
            owned_json = directory / "references/orphan.json"
            unrelated = directory / "local-notes.md"
            changed.write_text("drift\n")
            missing.unlink()
            owned.write_text("<!-- Generated from skills/spec-design-validator/references/orphan.md by scripts/build-distribution.py. Maintainers: edit the canonical file and rebuild. -->\n")
            owned_toml.write_text("# Generated by scripts/build-distribution.py; edit canonical skill resources.\n")
            owned_json.write_text(json.dumps({"$comment": "Canonical source: skills/spec-design-validator/references/orphan.json. Copies elsewhere are generated by scripts/build-distribution.py; edit the canonical file and rebuild."}))
            local_content = "Local instructions: run scripts/build-distribution.py after editing the rubric.\n"
            unrelated.write_text(local_content)
            result = self.build(root, check=True)
            self.assertNotEqual(result.returncode, 0)
            for path in (changed, missing, owned, owned_toml, owned_json):
                self.assertIn(str(path.relative_to(root)), result.stdout)
            result = self.build(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(owned.exists())
            self.assertFalse(owned_toml.exists())
            self.assertFalse(owned_json.exists())
            self.assertEqual(unrelated.read_text(), local_content)
            self.assertEqual(changed.read_text(), (payload(ROOT, SKILLS[0]) / "claude.md").read_text())
            result = self.build(root, check=True)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_codex_instructions_round_trip_del_and_unicode(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(Path(temporary))
            sentinel = "TOML round trip: café 東京 🐈 \x7f\n"
            canonical = root / "skills/spec-design-validator/SKILL.md"
            canonical.write_text(canonical.read_text() + "\n" + sentinel)
            result = self.build(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            for skill in SKILLS:
                document = tomllib.loads((payload(root, skill) / "codex.toml").read_text())
                self.assertIn(sentinel, document["developer_instructions"])


if __name__ == "__main__":
    unittest.main()
