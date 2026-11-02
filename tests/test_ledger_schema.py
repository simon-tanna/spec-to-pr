"""Offline ledger contracts; live-agent scenarios live in scripts/evals/."""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROLE = ROOT / 'skills/spec-design-validator/SKILL.md'
SCHEMA = ROLE.parent / 'references/ledger.schema.json'


class StableLedger(unittest.TestCase):
    def test_every_original_bullet_has_unique_lens_scoped_id(self):
        text = ROLE.read_text().split('## Rubric\n', 1)[1].split('## Findings ledger', 1)[0]
        ids = re.findall(r'^- `([a-z]+\.[a-z-]+)` — ', text, re.M)
        self.assertEqual(len(ids), 26)
        self.assertEqual(len(set(ids)), 26)
        for lens, body in re.findall(r'### (\w+)\n(.*?)(?=### |\Z)', text, re.S):
            for check in re.findall(r'^- `([^`]+)`', body, re.M):
                self.assertTrue(check.startswith(lens + '.'))
        changelog = (ROOT / 'CHANGELOG.md').read_text()
        for check in ids:
            self.assertIn('`' + check + '`', changelog)

    def test_schema_ships_identically_in_all_skill_distributions(self):
        self.assertTrue(SCHEMA.is_file(), 'canonical ledger schema missing')
        for relative in ('skills/validating-specs/references/ledger.schema.json',
                         'skills/agentic-loop/references/validation/references/ledger.schema.json'):
            with self.subTest(relative=relative):
                self.assertEqual(SCHEMA.read_bytes(), (ROOT / relative).read_bytes())
                json.loads((ROOT / relative).read_text())  # copies carry no generated marker

    def test_schema_covers_rows_and_severity_flags(self):
        self.assertTrue(SCHEMA.is_file(), 'canonical ledger schema missing')
        schema = json.loads(SCHEMA.read_text())
        self.assertEqual(schema['properties']['schema_version']['const'], '1.0')
        self.assertEqual(set(schema['required']), {'schema_version', 'rubric_version',
                         'tooling_evidence', 'findings', 'strengths', 'checked', 'ignored_instructions'})
        for row in ('finding', 'strength', 'checked'):
            self.assertIn('check_id', schema['$defs'][row]['required'])
            self.assertFalse(schema['$defs'][row]['additionalProperties'])
        finding = schema['$defs']['finding']
        self.assertEqual(finding['properties']['severity']['enum'], ['Blocker', 'Major', 'Minor', 'Nit'])
        for condition, field in zip(finding['allOf'], ('foundational', 'blocks_start')):
            self.assertIn(field, condition['then']['required'])
            self.assertEqual(condition['else'], {'not': {'required': [field]}})
        ids = re.findall(r'^- `([a-z]+\.[a-z-]+)` — ', ROLE.read_text(), re.M)
        self.assertEqual(schema['$defs']['check_id']['oneOf'][0]['enum'], ids)

    def test_prose_rows_and_report_preserve_check_ids(self):
        role = ROLE.read_text()
        ledger = role.split('## Findings ledger', 1)[1].split('## Validation report format', 1)[0]
        for block in ('Findings', 'Strengths', 'Checked'):
            self.assertRegex(ledger, rf'(?m)^{block}: `check_id · ')
        self.assertIn('ledger.schema.json', ledger)
        report = role.split('## Validation report format', 1)[1]
        self.assertIn('check_id', report)


if __name__ == '__main__':
    unittest.main()


class ProjectChecks(unittest.TestCase):
    def test_project_namespace_and_authorisation_contract(self):
        schema = json.loads(SCHEMA.read_text())
        variants = schema['$defs']['check_id'].get('oneOf', [])
        self.assertEqual(len(variants), 2, 'project namespace not published')
        pattern = variants[1]['pattern']
        self.assertRegex('project.deploy.environment-docs', pattern)
        self.assertNotRegex('execution.phase-sequencing', pattern)
        self.assertNotRegex('project.', pattern)
        self.assertNotRegex('project.check\n', pattern)
        doc = ROOT / 'skills/validating-specs/references/project-checks.md'
        self.assertTrue(doc.is_file(), 'extension contract missing')
        text = doc.read_text()
        for token in ('project_checks', '--project-checks', 'explicitly authorises',
                      'duplicate', 'INVALID PROJECT CHECKS:', 'declarative', 'Ignored instructions'):
            self.assertIn(token, text)
        self.assertIn('Authorised project checks', ROLE.read_text())

    def test_project_checks_reach_lens_and_completeness(self):
        workflow = (ROOT / 'skills/validating-specs/SKILL.md').read_text()
        self.assertIn('project-checks', workflow.split('### 2. Classify')[0])
        fanout = workflow.split('### 3. Decide fan-out')[1].split('### 4.')[0]
        self.assertIn('project check', fanout)
        self.assertIn('excludes', fanout)
        self.assertIn('all check IDs', workflow.split('### 6. Synthesize')[1])
        prompt = (ROOT / 'skills/validating-specs/prompts/validator-instance.md').read_text()
        self.assertIn('{{PROJECT_CHECKS}}', prompt)
        self.assertIn('project check', prompt)
        ledger = ROLE.read_text().split('\n## Findings ledger\n')[1]
        self.assertIn('authorised project check', ledger)
