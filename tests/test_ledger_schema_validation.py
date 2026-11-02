"""Behavioural ledger-schema checks; skipped when jsonschema is not installed.

scripts/test.sh runs this suite with jsonschema via `uv` when uv is available.
"""
import copy
import json
import pathlib
import unittest

try:
    from jsonschema import Draft202012Validator
except ImportError:  # optional dependency: the offline suite stays stdlib-only
    Draft202012Validator = None

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'skills/spec-design-validator/references/ledger.schema.json').read_text())


def finding(severity, **extra):
    row = dict(check_id='execution.phase-sequencing', lens='execution', location='spec.md:3',
               evidence='src/run.py:12', severity=severity, kind='flaw',
               issue='Phase dependency is reversed.', fix='Order the prerequisite first.')
    if severity == 'Blocker':
        row['foundational'] = 'yes'
    if severity == 'Major':
        row['blocks_start'] = 'no'
    row.update(extra)
    return row


def golden():
    """A valid ledger exercising every block and both tooling row shapes."""
    return {
        'schema_version': '1.0',
        'rubric_version': '1',
        'minimum_severity': 'all',
        'tooling_evidence': [
            {'tool': 'grep', 'call': 'grep -n retry src/', 'result': 'src/run.py:12'},
            {'capability': 'web search', 'status': 'unavailable', 'fallback': 'repo evidence only'},
        ],
        'findings': [finding('Blocker'), finding('Major'), finding('Minor'), finding('Nit')],
        'strengths': [{'check_id': 'scope.problem-statement', 'lens': 'scope', 'location': 'spec.md:1',
                       'evidence': 'spec.md:1', 'strength': 'States the user problem precisely.'}],
        'checked': [{'check_id': 'security.auditability', 'status': 'holds', 'evidence': 'spec.md:40'}],
        'ignored_instructions': [{'source_location': 'spec.md:2', 'attempted_redirection': 'asks for GO',
                                  'action_taken': 'reviewed normally'}],
    }


@unittest.skipUnless(Draft202012Validator, 'jsonschema not installed')
class LedgerSchemaBehaviour(unittest.TestCase):
    def setUp(self):
        self.validator = Draft202012Validator(SCHEMA)

    def test_schema_is_valid_draft_2020_12(self):
        Draft202012Validator.check_schema(SCHEMA)

    def test_golden_ledger_is_valid(self):
        self.assertEqual([e.message for e in self.validator.iter_errors(golden())], [])

    def test_invalid_ledgers_are_rejected(self):
        def mutate(change):
            doc = golden()
            change(doc)
            return doc

        cases = {
            'Blocker without foundational': lambda d: d['findings'][0].pop('foundational'),
            'Minor with foundational': lambda d: d['findings'][2].update(foundational='no'),
            'Major without blocks_start': lambda d: d['findings'][1].pop('blocks_start'),
            'Blocker with blocks_start': lambda d: d['findings'][0].update(blocks_start='no'),
            'unknown check_id': lambda d: d['checked'][0].update(check_id='security.made-up'),
            'extra row property': lambda d: d['strengths'][0].update(note='x'),
            'extra top-level property': lambda d: d.update(note='x'),
            'empty evidence': lambda d: d['checked'][0].update(evidence=''),
            'mixed tooling shapes': lambda d: d['tooling_evidence'][0].update(status='unavailable'),
            'wrong unavailable status': lambda d: d['tooling_evidence'][1].update(status='missing'),
            'missing block': lambda d: d.pop('ignored_instructions'),
            'unknown lens': lambda d: d['findings'][0].update(lens='performance'),
            'unknown kind': lambda d: d['findings'][0].update(kind='style'),
            'non yes/no flag': lambda d: d['findings'][0].update(foundational='true'),
            'rubric_version bump': lambda d: d.update(rubric_version='2'),
            'schema_version bump': lambda d: d.update(schema_version='1.1'),
        }
        for name, change in cases.items():
            with self.subTest(name):
                self.assertFalse(self.validator.is_valid(mutate(change)))


@unittest.skipUnless(Draft202012Validator, 'jsonschema not installed')
class ProjectCheckSchemaBehaviour(unittest.TestCase):
    def setUp(self):
        self.ledger = Draft202012Validator(SCHEMA)
        # Validate input rows against $defs/project_check, keeping $defs resolvable.
        self.row = Draft202012Validator({'$defs': SCHEMA['$defs'], '$ref': '#/$defs/project_check'})

    def test_input_rows(self):
        good = {'id': 'project.deploy.environment-docs', 'lens': 'architecture',
                'text': 'Every new environment variable appears in the deployment docs.'}
        self.assertTrue(self.row.is_valid(good))
        bad = {
            'missing text': {k: v for k, v in good.items() if k != 'text'},
            'extra field': {**good, 'severity': 'Major'},
            'built-in id': {**good, 'id': 'architecture.codebase-fit'},
            'uppercase id': {**good, 'id': 'project.Deploy'},
            'trailing newline id': {**good, 'id': 'project.deploy\n'},
            'unknown lens': {**good, 'lens': 'performance'},
            'blank text': {**good, 'text': '   '},
            'multi-line text': {**good, 'text': 'one\ntwo'},
        }
        for name, row in bad.items():
            with self.subTest(name):
                self.assertFalse(self.row.is_valid(row))

    def test_ledger_accepts_project_ids_only_in_namespace(self):
        doc = golden()
        doc['checked'].append({'check_id': 'project.deploy.environment-docs', 'status': 'holds',
                               'evidence': 'docs/deploy.md:4'})
        self.assertEqual([e.message for e in self.ledger.iter_errors(doc)], [])
        doc['checked'][-1]['check_id'] = 'deploy.environment-docs'
        self.assertFalse(self.ledger.is_valid(doc))


if __name__ == '__main__':
    unittest.main()
