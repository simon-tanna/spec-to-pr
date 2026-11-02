import pathlib, re, unittest, shutil, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
class Standalone(unittest.TestCase):
    def test_complete_portable_role(self):
        p = ROOT / 'skills/spec-design-validator/SKILL.md'
        self.assertTrue(p.exists(), 'standalone skill missing')
        text = p.read_text()
        self.assertNotRegex(text.lower().replace("claude.md", "rules.md"), r"\b(controller|dispatch\w*|subagent\w*|codex|claude)\b")
        for block in ('Tooling evidence:', 'Findings:', 'Strengths:', 'Checked:', 'Ignored instructions:'):
            self.assertIn(block, text)
        self.assertIn('## Validation report format', text)

    def test_original_rubric_preserved(self):
        original = (ROOT / 'tests/fixtures/validator-rubric-v0.4.0.txt').read_text().splitlines()
        skill = (ROOT / 'skills/spec-design-validator/SKILL.md').read_text()
        self.assertEqual(len(original), 26)
        for bullet in original:
            self.assertEqual(skill.count(bullet), 1)

    def test_canonical_changes_propagate_with_missing_intermediates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for name in ('scripts', 'skills', 'adapters', 'agents'):
                shutil.copytree(ROOT / name, root / name)
            skill = root / 'skills/spec-design-validator/SKILL.md'
            skill.write_text(skill.read_text() + '\nCanonical propagation sentinel.\n\n## Later section\nNot report material.\n')
            for name in ('validator-role.md', 'report-format.md'):
                (root / 'skills/validating-specs/references' / name).unlink()
            command = [sys.executable, str(root / 'scripts/build-distribution.py')]
            subprocess.run(command, check=True, capture_output=True)
            subprocess.run(command + ['--check'], check=True, capture_output=True)
            for name in ('agents/spec-design-validator.md',
                         'skills/validating-specs/references/validator-role.md',
                         'skills/validating-specs/references/report-format.md',
                         'skills/agentic-loop/references/validation/references/validator-role.md',
                         'skills/agentic-loop/references/validation/references/report-format.md'):
                self.assertIn('Canonical propagation sentinel.', (root / name).read_text())
                if name.endswith('report-format.md'):
                    self.assertNotIn('Not report material.', (root / name).read_text())
