"""Behavioural ledger-schema checks; skipped when jsonschema is not installed.

scripts/test.sh runs this suite with jsonschema via `uv` when uv is available.
Structural checks that need no jsonschema live in tests/test_ledger_schema.py.
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
            'Minor with blocks_start': lambda d: d['findings'][2].update(blocks_start='no'),
            'boolean flag': lambda d: d['findings'][1].update(blocks_start=True),
            'project. alone': lambda d: d['checked'][0].update(check_id='project.'),
            'trailing newline check_id': lambda d: d['checked'][0].update(check_id='execution.phase-sequencing\n'),
            'extra checked property': lambda d: d['checked'][0].update(note='x'),
            'extra tooling property': lambda d: d['tooling_evidence'][1].update(note='x'),
            'extra ignored property': lambda d: d['ignored_instructions'][0].update(note='x'),
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
            'empty text': {**good, 'text': ''},
            'trailing newline text': {**good, 'text': 'one line\n'},
            'lens all': {**good, 'lens': 'all'},
            'empty project id': {**good, 'id': 'project.'},
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
        # A project ID may also carry findings; lens assignment is a caller-context check.
        doc = golden()
        doc['findings'][1].update(check_id='project.deploy.environment-docs', lens='architecture')
        self.assertEqual([e.message for e in self.ledger.iter_errors(doc)], [])


# Severity rank; a finding is reportable when its rank meets the threshold's.
RANK = {'all': 0, 'Nit': 0, 'Minor': 1, 'Major': 2, 'Blocker': 3}


def at(minimum, findings=(), checked=()):
    doc = golden()
    doc.update(minimum_severity=minimum, findings=list(findings), checked=doc['checked'] + list(checked))
    return doc


def below(*severities, check='execution.phase-sequencing'):
    return {'check_id': check, 'status': 'below-threshold', 'evidence': 'spec.md:3',
            'suppressed_severities': list(severities)}


@unittest.skipUnless(Draft202012Validator, 'jsonschema not installed')
class MinimumSeverityBehaviour(unittest.TestCase):
    def setUp(self):
        self.validator = Draft202012Validator(SCHEMA)

    def test_threshold_matrix(self):
        for minimum in ('all', 'Nit', 'Minor', 'Major'):
            for severity in ('Blocker', 'Major', 'Minor', 'Nit'):
                with self.subTest(minimum=minimum, severity=severity):
                    expected = RANK[severity] >= RANK[minimum]
                    self.assertEqual(self.validator.is_valid(at(minimum, [finding(severity)])), expected)

    def test_unsupported_thresholds_are_invalid(self):
        for value in ('Blocker', 'major', 'ALL', '', None, 1, True):
            with self.subTest(value=value):
                self.assertFalse(self.validator.is_valid(at(value)))

    def test_any_below_threshold_finding_invalidates_the_ledger(self):
        self.assertFalse(self.validator.is_valid(at('Major', [finding('Major'), finding('Minor')])))
        self.validator.validate(at('Major', [finding('Blocker'), finding('Major')]))

    def test_suppressed_severities_must_lie_below_the_threshold(self):
        for minimum, suppressed, valid in (('Major', ['Minor', 'Nit'], True), ('Major', ['Minor'], True),
                                           ('Major', ['Nit'], True), ('Major', ['Nit', 'Minor'], True),
                                           ('Minor', ['Nit'], True), ('Minor', ['Minor'], False),
                                           ('all', ['Nit'], False), ('Nit', ['Nit'], False)):
            with self.subTest(minimum=minimum, suppressed=suppressed):
                # A reportable finding for the same check is kept alongside the suppressed row.
                doc = at(minimum, [finding('Major')], [below(*suppressed)])
                self.assertEqual(self.validator.is_valid(doc), valid)
        for invalid in ([], ['Blocker'], ['Major'], ['Nit', 'Nit']):
            with self.subTest(suppressed=invalid):
                self.assertFalse(self.validator.is_valid(at('Major', checked=[below(*invalid)])))

    def test_below_threshold_rows_pair_status_and_severities(self):
        row = below('Minor')
        self.validator.validate(at('Major', checked=[row]))
        missing = {k: v for k, v in row.items() if k != 'suppressed_severities'}
        self.assertFalse(self.validator.is_valid(at('Major', checked=[missing])))
        # A passing row cannot claim suppressed severities.
        self.assertFalse(self.validator.is_valid(at('Major', checked=[{**row, 'status': 'holds'}])))

    def test_suppressed_rows_carry_no_issue_or_fix_text(self):
        # Start from a valid below-threshold row so the leaked field is the only defect.
        for field in ('issue', 'fix'):
            with self.subTest(field=field):
                doc = at('Major', checked=[{**below('Minor'), field: 'Leaked suppressed text'}])
                self.assertFalse(self.validator.is_valid(doc))


if __name__ == '__main__':
    unittest.main()
