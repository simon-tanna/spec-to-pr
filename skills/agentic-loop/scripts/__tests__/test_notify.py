"""Notification routing with recording stubs; no external messages are sent."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'notify.sh'


class NotifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.calls = self.root / 'calls'
        for name in ('gh', 'curl', 'deliver'):
            stub = self.bin / name
            stub.write_text('#!/bin/sh\n'
                            'if [ "$1" = auth ]; then exit 0; fi\n'
                            'printf "%s\\n" "$0 $*" >> "$NOTIFY_TEST_CALLS"\n'
                            'cat >> "$NOTIFY_TEST_CALLS"\n')
            stub.chmod(0o755)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith('AGENTIC_') and k != 'GITHUB_ACTIONS'}
        self.env.update(PATH=str(self.bin) + os.pathsep + os.environ['PATH'],
                        NOTIFY_TEST_CALLS=str(self.calls))

    def metadata(self, run_id, content):
        run = self.root / '.agentic-loop' / run_id
        run.mkdir(parents=True, exist_ok=True)
        (run / 'run-context.json').write_text(content)
        return run

    def notify(self, run_id, **env):
        return subprocess.run(['bash', str(SCRIPT), 'blocked', run_id, '-'],
                              cwd=self.root, env=self.env | env, input='Decision required\n',
                              text=True, capture_output=True)

    def test_issueless_metadata_falls_back_even_for_numeric_id(self):
        for run_id in ('inline-spec-abc12345', '42'):
            with self.subTest(run_id=run_id):
                run = self.metadata(run_id, '{"issue":null}')
                (run / 'open-questions.md').write_text('Decision required\n')
                (run / 'NEEDS_INPUT').touch()
                result = self.notify(run_id)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('Decision required', (run / 'notifications.md').read_text())
                self.assertIn('::agentic-notify', result.stdout)
                self.assertEqual((run / 'open-questions.md').read_text(), 'Decision required\n')
                self.assertTrue((run / 'NEEDS_INPUT').exists())
                self.assertFalse(self.calls.exists())

    def test_metadata_issue_and_legacy_numeric_id_use_github(self):
        for run_id, issue in (('named-run', 73), ('legacy', '74')):
            self.metadata(run_id, json.dumps({'issue': issue}))
            result = self.notify(run_id)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f'issue comment {issue} --body-file -', self.calls.read_text())
        self.assertEqual(self.notify('42').returncode, 0)
        self.assertIn('issue comment 42 --body-file -', self.calls.read_text())

    def test_nonnumeric_id_without_metadata_uses_file(self):
        result = self.notify('inline-spec-abc12345', AGENTIC_IO_ADAPTER='github')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / '.agentic-loop/inline-spec-abc12345/notifications.md').exists())
        self.assertFalse(self.calls.exists())

    def test_malformed_metadata_stops_before_comment(self):
        for content in ('{', '{}', '[]', '{"issue":0}', '{"issue":"bad"}', '{"issue":true}'):
            with self.subTest(content=content):
                self.metadata('42', content)
                result = self.notify('42')
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.calls.exists())

    def test_explicit_adapters_do_not_depend_on_issue_metadata(self):
        run = self.metadata('task', '{')
        self.assertEqual(self.notify('task', AGENTIC_IO_ADAPTER='file').returncode, 0)
        self.assertTrue((run / 'notifications.md').exists())
        self.assertEqual(self.notify('task', AGENTIC_IO_ADAPTER='command',
                                     AGENTIC_NOTIFY_COMMAND=str(self.bin / 'deliver')).returncode, 0)
        self.assertIn('deliver blocked task', self.calls.read_text())
        self.assertEqual(self.notify('task', AGENTIC_IO_ADAPTER='webhook',
                                     AGENTIC_NOTIFY_WEBHOOK='https://example.invalid/notify').returncode, 0)
        self.assertIn('curl -fsS -X POST', self.calls.read_text())

    def test_fallback_preserves_pr_adapter_config(self):
        config = self.root / '.agentic-loop.config.json'
        config.write_text('{"io":{"adapter":"github"}}')
        self.metadata('task', '{"issue":null}')
        result = self.notify('task')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / '.agentic-loop/task/notifications.md').exists())
        self.assertEqual(json.loads(config.read_text())['io']['adapter'], 'github')
        self.assertFalse(self.calls.exists())


if __name__ == '__main__':
    unittest.main()
