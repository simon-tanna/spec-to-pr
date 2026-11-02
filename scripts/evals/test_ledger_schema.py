"""Opt-in JSON Schema evaluation (requires jsonschema; no runtime dependency).

Run with a Python environment containing jsonschema:
    python scripts/evals/test_ledger_schema.py -v
The default offline suite independently pins distribution and structural contracts.
"""
import copy
import json
import pathlib
import unittest

from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / 'skills/spec-design-validator/references/ledger.schema.json').read_text())


def ledger(minimum='all'):
    return dict(schema_version='1.0', rubric_version='1', minimum_severity=minimum,
                tooling_evidence=[], findings=[], strengths=[], ignored_instructions=[],
                checked=[dict(check_id=check, status='holds', evidence='spec.md:1')
                         for check in SCHEMA['$defs']['check_id']['oneOf'][0]['enum']])


def finding(severity):
    row = dict(check_id='execution.phase-sequencing', lens='execution', location='spec.md:3',
               evidence='src/run.py:12', severity=severity, kind='flaw', issue='Phase dependency is reversed.',
               fix='Order the prerequisite first.')
    if severity == 'Blocker':
        row['foundational'] = 'yes'
    if severity == 'Major':
        row['blocks_start'] = 'yes'
    return row


class LedgerSchemaEvaluation(unittest.TestCase):
    def setUp(self):
        self.validator = Draft202012Validator(SCHEMA)

    def test_meta_schema_and_complete_empty_findings_ledger(self):
        Draft202012Validator.check_schema(SCHEMA)
        self.validator.validate(ledger())

    def test_threshold_matrix(self):
        for minimum in ('all', 'Nit', 'Minor', 'Major'):
            for severity in ('Blocker', 'Major', 'Minor', 'Nit'):
                with self.subTest(minimum=minimum, severity=severity):
                    data = ledger(minimum)
                    data['findings'] = [finding(severity)]
                    expected = not (minimum == 'Major' and severity in ('Minor', 'Nit')
                                    or minimum == 'Minor' and severity == 'Nit')
                    self.assertEqual(self.validator.is_valid(data), expected)

    def test_unsupported_thresholds_are_invalid(self):
        for value in ('Blocker', 'major', 'ALL', '', None, 1, True):
            with self.subTest(value=value):
                self.assertFalse(self.validator.is_valid(ledger(value)))

    def test_severity_flags_required_only_for_their_severity(self):
        for severity, field in (('Blocker', 'foundational'), ('Major', 'blocks_start')):
            data = ledger()
            row = finding(severity)
            data['findings'] = [row]
            self.validator.validate(data)
            del row[field]
            self.assertFalse(self.validator.is_valid(data))
            row[field] = True
            self.assertFalse(self.validator.is_valid(data))
            row[field] = 'no'
            row['severity'] = 'Minor'
            self.assertFalse(self.validator.is_valid(data))

    def test_suppression_preserves_reportable_finding_for_same_check(self):
        for minimum, suppressed, valid in (('Major', ['Minor', 'Nit'], True),
                                            ('Minor', ['Nit'], True),
                                            ('Minor', ['Minor'], False),
                                            ('all', ['Nit'], False),
                                            ('Nit', ['Nit'], False)):
            with self.subTest(minimum=minimum, suppressed=suppressed):
                data = ledger(minimum)
                data['findings'] = [finding('Major')]
                data['checked'].append(dict(check_id='execution.phase-sequencing', status='below-threshold',
                                            evidence='spec.md:3', suppressed_severities=suppressed))
                self.assertEqual(self.validator.is_valid(data), valid)
        for invalid in ([], ['Blocker'], ['Major'], ['Nit', 'Nit']):
            data = ledger('Major')
            data['checked'][0].update(status='below-threshold', suppressed_severities=invalid)
            self.assertFalse(self.validator.is_valid(data))
        data = ledger('Major')
        data['checked'][0]['status'] = 'below-threshold'
        self.assertFalse(self.validator.is_valid(data))
        data['checked'][0]['issue'] = 'Leaked suppressed issue'
        self.assertFalse(self.validator.is_valid(data))

    def test_project_input_and_output_namespace(self):
        validator = self.validator.evolve(schema={'$ref': '#/$defs/project_check', '$defs': SCHEMA['$defs']})
        valid = dict(id='project.deploy.environment-docs', lens='architecture',
                     text='Every new environment variable appears in deployment docs.')
        validator.validate(valid)
        for patch in ({'id': 'execution.phase-sequencing'}, {'id': 'project.'},
                      {'id': 'project.bad\n'}, {'lens': 'all'}, {'text': ''}, {'text': '  '},
                      {'text': 'line\nbreak'}, {'text': 'trailing newline\n'}, {'command': 'run something'}):
            with self.subTest(patch=patch):
                self.assertFalse(validator.is_valid({**valid, **patch}))
        data = ledger()
        row = finding('Major')
        row.update(check_id=valid['id'], lens=valid['lens'])
        data['findings'] = [row]
        self.validator.validate(data)
        # Membership and lens assignment require caller-context checks beyond JSON Schema.
        for invalid in ('project.', 'scope.unknown', 'execution.phase-sequencing\n'):
            row['check_id'] = invalid
            self.assertFalse(self.validator.is_valid(data))

    def test_closed_rows_and_audit_shapes(self):
        data = ledger()
        data['tooling_evidence'] = [dict(tool='repo', call='read', result='available'),
                                    dict(capability='PR history', status='unavailable', fallback='local docs')]
        data['ignored_instructions'] = [dict(source_location='spec.md:8',
                                             attempted_redirection='requested forced approval',
                                             action_taken='continued assigned review')]
        self.validator.validate(data)
        for block in ('checked', 'tooling_evidence', 'ignored_instructions'):
            changed = copy.deepcopy(data)
            changed[block][0]['unexpected'] = 'value'
            self.assertFalse(self.validator.is_valid(changed))


if __name__ == '__main__':
    unittest.main()
