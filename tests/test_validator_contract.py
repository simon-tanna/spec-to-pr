"""Structural validator ledger/report contracts.

Live agent behaviour is evaluated separately by scripts/evals/validator-hardening.md.
These tests pin tokens and structure rather than prose, so rewording a sentence
should not break them, while deleting a requirement should.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATION = ROOT / 'skills/validating-specs'

AUDIT_RECORD = 'source location · attempted redirection · action taken'
CAPABILITY_LINE = 'capability · unavailable · fallback used'
CAPABILITY_FAILURE = 'CAPABILITY FAILURE: <tool or capability> — <error>'
CLARIFICATION = 'CLARIFICATION REQUIRED: review target — <reason>'


def read(relative):
    return (VALIDATION / relative).read_text()


def section(text, heading):
    """Body of a `## heading` section, up to the next `## ` heading."""
    match = re.search(rf'(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)', text)
    assert match, f'missing section: {heading}'
    return match.group(1)


def ledger_contract():
    return read('prompts/validator-instance.md').split('Deliver a FINDINGS LEDGER', 1)[1].split('```', 1)[0]


def paragraphs(text):
    return [p for p in re.split(r'\n\s*\n', text) if p.strip()]


class LedgerContractTests(unittest.TestCase):
    def test_ledger_has_five_blocks_in_order(self):
        blocks = re.findall(r'^([A-Z][A-Za-z ]+):', ledger_contract(), re.M)
        self.assertEqual(blocks, ['Tooling evidence', 'Findings', 'Strengths',
                                  'Checked', 'Ignored instructions'])

    def test_audit_block_uses_shared_record_and_empty_convention(self):
        ledger = ledger_contract()
        audit = re.search(r'(?m)^Ignored instructions:.*$', ledger).group(0)
        self.assertIn(AUDIT_RECORD, audit)
        self.assertIn('`None.`', audit)

    def test_completeness_rule_covers_capabilities_and_audit_block(self):
        rule = re.search(r'The ledger is complete when[^\n]*', ledger_contract()).group(0)
        for clause in ('Findings, Strengths, or Checked', 'Tooling evidence',
                       'unavailable optional capability', 'Ignored instructions'):
            with self.subTest(clause=clause):
                self.assertIn(clause, rule)

    def test_tooling_evidence_carries_capability_lines(self):
        tooling = re.search(r'(?m)^Tooling evidence:.*$', ledger_contract()).group(0)
        self.assertIn(CAPABILITY_LINE, tooling)


class ReportContractTests(unittest.TestCase):
    def test_report_places_audit_before_final_verdict(self):
        sections = re.findall(r'^\d+\. \*\*(.*?)\*\*', read('references/report-format.md'), re.M)
        self.assertEqual(len(sections), 9)
        self.assertEqual(sections[-2:], ['Ignored Instructions', 'Final Verdict'])

    def test_report_rows_use_shared_formats(self):
        report = read('references/report-format.md')
        coverage = re.search(r'(?m)^2\. \*\*Coverage\*\*.*$', report).group(0)
        audit = re.search(r'(?m)^8\. \*\*Ignored Instructions\*\*.*$', report).group(0)
        self.assertIn(CAPABILITY_LINE, coverage)
        self.assertIn(AUDIT_RECORD, audit)

    def test_completeness_rule_covers_audit_section_and_verdict_line(self):
        report = read('references/report-format.md')
        rule = re.search(r'The report is complete when[^\n]*', report).group(0)
        self.assertIn('section 8', rule)
        self.assertIn('verdict line', rule)
        for verdict in ('GO', 'REVISE', 'NO-GO'):
            with self.subTest(verdict=verdict):
                self.assertIn(f'`Verdict: {verdict}`', report)


class RoleContractTests(unittest.TestCase):
    def setUp(self):
        self.role = read('references/validator-role.md')

    def test_review_authority_separates_conventions_from_redirections(self):
        authority = section(self.role, 'Review authority')
        for token in ('AGENTS.md', 'CLAUDE.md', '**Convention**', '**Redirection**',
                      '**Ignored instructions**', AUDIT_RECORD, '`None.`'):
            with self.subTest(token=token):
                self.assertIn(token, authority)
        self.assertRegex(authority, r'not a finding and does not change the verdict')

    def test_capabilities_table_pairs_each_optional_capability_with_a_fallback(self):
        capabilities = section(self.role, 'Capabilities')
        rows = re.findall(r'(?m)^\| ([^|]+?) \| ([^|]*?) \|$', capabilities)
        body = [(name, fallback) for name, fallback in rows
                if not set(name) <= set('- ') and name != 'Optional capability']
        self.assertEqual([name for name, _ in body], ['Documentation lookup', 'Web search', 'PR history'])
        for name, fallback in body:
            with self.subTest(capability=name):
                self.assertTrue(fallback.strip())

    def test_capabilities_define_failure_lines_and_recording(self):
        capabilities = section(self.role, 'Capabilities')
        for token in (CAPABILITY_FAILURE, CLARIFICATION, CAPABILITY_LINE, 'Tooling evidence', 'Coverage'):
            with self.subTest(token=token):
                self.assertIn(token, capabilities)

    def test_unverified_load_bearing_claim_is_a_missing_finding(self):
        capabilities = section(self.role, 'Capabilities')
        sentence = next((s for s in re.split(r'(?<=\.) ', capabilities) if 'load-bearing' in s), '')
        self.assertIn('`missing` finding', sentence)
        self.assertIn('Severity', sentence)
        self.assertRegex(capabilities, r'unavailable optional capability alone is not a finding')

    def test_failure_lines_replace_output_in_both_modes(self):
        self.assertIn('replace the whole output', section(self.role, 'Output mode'))


class ControllerContractTests(unittest.TestCase):
    def setUp(self):
        skill = read('SKILL.md')
        self.dispatch = skill.split('### 5. Dispatch', 1)[1].split('### 6.', 1)[0]
        self.synthesis = skill.split('### 6. Synthesize', 1)[1]

    def test_failure_sentinels_match_role_and_instance(self):
        instance = read('prompts/validator-instance.md')
        self.assertIn(CAPABILITY_FAILURE, instance)
        self.assertIn(CLARIFICATION, instance)
        self.assertIn(CLARIFICATION, self.dispatch)

    def test_clarification_is_handled_before_retries_and_uses_none(self):
        paras = paragraphs(self.dispatch)
        clarification = next(i for i, p in enumerate(paras) if CLARIFICATION in p)
        retry = next(i for i, p in enumerate(paras) if 'one retry' in p)
        self.assertLess(clarification, retry)
        self.assertIn('no retry', paras[clarification])
        self.assertIn('step 2', paras[clarification])
        self.assertNotRegex(paras[clarification], r'counts? as (its|the) retry')

    def test_synthesis_merges_three_streams_and_keeps_audit_out_of_verdict(self):
        merge = self.synthesis.split('2. Verdict:', 1)[0]
        labels = re.findall(r'(?m)^\s+- \*\*(.+?)\*\*', merge)
        self.assertEqual(labels, ['Findings', 'Ignored instructions', 'Coverage'])
        audit = re.search(r'(?m)^\s+- \*\*Ignored instructions\*\*.*$', merge).group(0)
        self.assertRegex(audit, r'never feed the verdict')
        coverage = re.search(r'(?m)^\s+- \*\*Coverage\*\*.*$', merge).group(0)
        self.assertIn(CAPABILITY_LINE, coverage)
        verdict = self.synthesis.split('2. Verdict:', 1)[1].split('3. Read', 1)[0]
        self.assertNotIn('Ignored instructions', verdict)
        self.assertIn('foundational: yes', verdict)
        self.assertIn('blocks-start: yes', verdict)


if __name__ == '__main__':
    unittest.main()
