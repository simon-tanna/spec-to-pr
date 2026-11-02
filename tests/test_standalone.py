"""The standalone spec-design-validator skill: portability, rubric, independence, generation."""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/spec-design-validator/SKILL.md'
REPORT_HEADING = '## Validation report format'


def frontmatter(text):
    match = re.match(r'(?s)---\n(.*?)\n---\n', text)
    assert match, 'missing frontmatter'
    return dict(line.split(': ', 1) for line in match.group(1).splitlines() if ': ' in line)


class Standalone(unittest.TestCase):
    def test_complete_portable_role(self):
        self.assertTrue(SKILL.exists(), 'standalone skill missing')
        text = SKILL.read_text()
        # A skill-only install has no controller; the role must not depend on one.
        # CLAUDE.md is a project file the reviewer reads, so it is exempt.
        self.assertNotRegex(text.lower().replace("claude.md", "rules.md"), r"\b(controller|dispatch\w*|subagent\w*|codex|claude)\b")
        for block in ('Tooling evidence:', 'Findings:', 'Strengths:', 'Checked:', 'Ignored instructions:'):
            self.assertIn(block, text)
        self.assertIn(REPORT_HEADING, text)
        self.assertIn('Leave the working tree, index, and commit history exactly as you found them.', text)
        self.assertNotIn('beside this file', text)

    def test_frontmatter_names_the_skill_and_its_reviewer(self):
        meta = frontmatter(SKILL.read_text())
        self.assertEqual(meta.get('name'), SKILL.parent.name)
        description = meta.get('description', '')
        self.assertIn('did not write', description)
        self.assertIn('validating-specs', description)

    def test_author_self_review_is_refused_not_permitted(self):
        text = SKILL.read_text()
        for permissive in ('## Independent inline review', 'can review it inline'):
            with self.subTest(permissive=permissive):
                self.assertNotIn(permissive, text)

    def test_original_rubric_preserved_under_its_lens(self):
        rows = [line.split('\t', 1) for line in (ROOT / 'tests/fixtures/validator-rubric-v0.4.0.txt').read_text().splitlines()]
        self.assertEqual(len(rows), 26)
        text = SKILL.read_text()
        lenses = dict(re.findall(r'(?ms)^### (\w+)\n(.*?)(?=^##)', text))
        self.assertEqual(sorted(lenses), sorted({lens for lens, _ in rows}))
        for lens, bullet in rows:
            with self.subTest(bullet=bullet[:40]):
                self.assertEqual(text.count(bullet), 1)
                self.assertIn(bullet, lenses[lens])


class Generation(unittest.TestCase):
    def copy_repo(self, tmp):
        root = pathlib.Path(tmp)
        for name in ('scripts', 'skills', 'adapters', 'agents'):
            shutil.copytree(ROOT / name, root / name)
        return root, [sys.executable, str(root / 'scripts/build-distribution.py')]

    def build(self, command):
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_canonical_changes_propagate_with_missing_intermediates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, command = self.copy_repo(tmp)
            skill = root / 'skills/spec-design-validator/SKILL.md'
            text = skill.read_text().replace(REPORT_HEADING, '## Earlier section\n\nNot report material.\n\n' + REPORT_HEADING, 1)
            skill.write_text(text + '\nCanonical propagation sentinel.\n')
            for name in ('validator-role.md', 'report-format.md'):
                (root / 'skills/validating-specs/references' / name).unlink()
            self.build(command)
            self.build(command + ['--check'])
            for name in ('agents/spec-design-validator.md',
                         'skills/validating-specs/references/validator-role.md',
                         'skills/validating-specs/references/report-format.md',
                         'skills/agentic-loop/references/validation/references/validator-role.md',
                         'skills/agentic-loop/references/validation/references/report-format.md'):
                generated = (root / name).read_text()
                with self.subTest(name=name):
                    self.assertIn('Canonical propagation sentinel.', generated)
                    if name.endswith('report-format.md'):
                        self.assertNotIn('Not report material.', generated)
                    else:
                        self.assertIn('Not report material.', generated)

    def test_build_fails_loudly_on_a_broken_report_section(self):
        cases = {
            'missing heading': lambda t: t.replace(REPORT_HEADING, '## Report', 1),
            'section after report': lambda t: t + '\n## Later section\n\nStray.\n',
        }
        for case, mutate in cases.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root, command = self.copy_repo(tmp)
                skill = root / 'skills/spec-design-validator/SKILL.md'
                skill.write_text(mutate(skill.read_text()))
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(REPORT_HEADING, result.stderr + result.stdout)
                self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
