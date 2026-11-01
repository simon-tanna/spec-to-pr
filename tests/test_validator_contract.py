"""Structural ledger/report contracts; live agent behaviour is evaluated separately."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATION = ROOT / 'skills/validating-specs'


class ValidatorContractTests(unittest.TestCase):
    def test_instance_ledger_has_five_blocks_and_empty_audit_convention(self):
        prompt = (VALIDATION / 'prompts/validator-instance.md').read_text()
        ledger = prompt.split('Deliver a FINDINGS LEDGER', 1)[1].split('```', 1)[0]
        blocks = re.findall(r'^([A-Z][A-Za-z ]+):', ledger, re.M)
        self.assertEqual(blocks, ['Tooling evidence', 'Findings', 'Strengths',
                                  'Checked', 'Ignored instructions'])
        self.assertIn('source location · attempted redirection · action taken', ledger)
        self.assertRegex(ledger, r'Ignored instructions:.*`None\.`')
        self.assertIn('every bullet', ledger)
        self.assertIn('Findings, Strengths, or Checked', ledger)

    def test_report_places_audit_before_final_verdict(self):
        report = (VALIDATION / 'references/report-format.md').read_text()
        sections = re.findall(r'^\d+\. \*\*(.*?)\*\*', report, re.M)
        self.assertEqual(sections[-2:], ['Ignored Instructions', 'Final Verdict'])
        self.assertEqual(len(sections), 9)
        self.assertIn('every ignored-instruction record', report)
        self.assertIn('its last line is a verdict line', report)

    def test_synthesis_preserves_audit_outside_verdict_calculation(self):
        synthesis = (VALIDATION / 'SKILL.md').read_text().split('### 6. Synthesize', 1)[1]
        self.assertIn('Ignored instructions', synthesis)
        self.assertIn('source location and attempted redirection', synthesis)
        self.assertIn('separate from findings', synthesis)
        verdict = synthesis.split('Verdict:', 1)[1].split('3. Read', 1)[0]
        self.assertNotIn('Ignored instructions', verdict)
        self.assertIn('foundational: yes', verdict)
        self.assertIn('blocks-start: yes', verdict)


if __name__ == '__main__':
    unittest.main()
