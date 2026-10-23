"""Interactive initialization integration tests using disposable local remotes."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'init-run.sh'

class InitRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.repo = root / 'repo'
        self.repo.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        (self.repo / 'tracked').write_text('original\n')
        self.git('add', '.')
        self.git('commit', '-m', 'initial')
        subprocess.run(['git', 'init', '--bare', str(root / 'remote')], check=True, capture_output=True)
        self.git('remote', 'add', 'origin', str(root / 'remote'))
        self.git('push', '-u', 'origin', 'main')
        self.source = self.repo / 'My Feature.md'
        self.source.write_text('Implement a feature.\n')
    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.repo, text=True, capture_output=True, check=True).stdout.strip()
    def run_init(self, *args, ok=True):
        result = subprocess.run(['bash', str(SCRIPT), '--source-file', str(self.source), *args], cwd=self.repo, text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, ok, result.stderr)
        return json.loads(result.stdout) if ok else result.stderr
    def test_identity_source_and_resume(self):
        original = self.source.read_bytes()
        result = self.run_init()
        expected = 'my-feature-' + hashlib.sha256(original).hexdigest()[:8]
        self.assertEqual(result['run_id'], expected)
        self.assertEqual(result['branch'], 'feat/' + expected)
        self.assertEqual((self.repo / result['run_dir'] / 'source.md').read_bytes(), original)
        self.assertEqual(self.source.read_bytes(), original)
        metadata = self.repo / result['run_dir'] / 'run-context.json'
        before = metadata.read_bytes()
        self.assertTrue(self.run_init()['resumed'])
        self.assertEqual(before, metadata.read_bytes())
    def test_dirty_index_and_worktree_refused_before_branch(self):
        (self.repo / 'tracked').write_text('dirty\n')
        self.run_init(ok=False)
        self.git('add', 'tracked')
        self.run_init(ok=False)
        self.assertEqual(self.git('branch', '--show-current'), 'main')
        self.assertFalse((self.repo / '.agentic-loop').exists())
    def test_base_precedence(self):
        for branch in ['configured', 'body', 'label', 'explicit']:
            self.git('branch', branch)
            self.git('push', 'origin', branch)
        (self.repo / '.agentic-loop.config.json').write_text('{"base_ref":"configured"}')
        self.git('add', '.agentic-loop.config.json')
        self.git('commit', '-m', 'config')
        result = self.run_init('--issue-base', 'body', '--label-base', 'label', '--base-ref', 'explicit')
        self.assertEqual(result['base_ref'], 'explicit')
    def test_config_beats_body_and_label(self):
        self.git('branch', 'configured')
        self.git('push', 'origin', 'configured')
        (self.repo / '.agentic-loop.config.json').write_text('{"base_ref":"configured"}')
        self.git('add', '.')
        self.git('commit', '-m', 'config')
        self.assertEqual(self.run_init('--issue-base', 'missing', '--label-base', 'missing')['base_ref'], 'configured')
    def test_missing_remote_base_and_detached_refused(self):
        self.run_init('--base-ref', 'missing', ok=False)
        self.git('remote', 'set-url', 'origin', str(self.repo / 'absent'))
        self.run_init(ok=False)
        self.git('checkout', '--detach')
        self.run_init(ok=False)
        self.assertFalse((self.repo / '.agentic-loop').exists())
    def test_branch_collision(self):
        self.git('branch', 'feat/existing')
        self.run_init('--branch', 'feat/existing', ok=False)
        self.assertEqual(self.git('branch', '--show-current'), 'main')
    def test_issue_identity_and_changed_source_rejected(self):
        result = self.run_init('--issue', '42', '--title', 'A feature')
        self.assertEqual(result['run_id'], '42')
        self.assertEqual(result['branch'], 'feat/42-a-feature')
        self.source.write_text('changed')
        self.run_init('--issue', '42', '--title', 'A feature', ok=False)
    def test_resume_on_wrong_branch_and_changed_base_rejected(self):
        result = self.run_init()
        self.run_init('--base-ref', 'other', ok=False)
        self.git('checkout', 'main')
        self.run_init('--run-id', result['run_id'], ok=False)
    def test_body_beats_label_without_config(self):
        self.git('branch', 'body')
        self.git('push', 'origin', 'body')
        self.assertEqual(self.run_init('--issue-base', 'body', '--label-base', 'missing')['base_ref'], 'body')
    def test_label_without_body_or_config(self):
        self.git('branch', 'label')
        self.git('push', 'origin', 'label')
        self.assertEqual(self.run_init('--label-base', 'label')['base_ref'], 'label')
    def test_remote_branch_collision(self):
        self.git('push', 'origin', 'main:refs/heads/feat/existing')
        self.run_init('--branch', 'feat/existing', ok=False)
        self.assertEqual(self.git('branch', '--show-current'), 'main')
    def test_tracked_source_snapshot_survives_branch_change(self):
        self.git('branch', 'base')
        self.git('push', 'origin', 'base')
        original = self.source.read_bytes()
        self.git('add', self.source.name)
        self.git('commit', '-m', 'source')
        result = self.run_init('--base-ref', 'base')
        self.assertEqual((self.repo / result['run_dir'] / 'source.md').read_bytes(), original)
    def test_base_cannot_introduce_storage_symlink(self):
        outside = Path(self.tmp.name) / 'outside'
        outside.mkdir()
        storage = self.repo / '.agentic-loop'
        storage.symlink_to(outside, target_is_directory=True)
        self.git('add', '.agentic-loop')
        self.git('commit', '-m', 'base storage symlink')
        self.git('branch', 'unsafe-base')
        self.git('push', 'origin', 'unsafe-base')
        storage.unlink()
        self.git('add', '.agentic-loop')
        self.git('commit', '-m', 'remove storage symlink')
        self.run_init('--base-ref', 'unsafe-base', ok=False)
        self.assertEqual(self.git('branch', '--show-current'), 'main')
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse(storage.exists())
    def test_base_cannot_introduce_existing_run_storage(self):
        storage = self.repo / '.agentic-loop' / '42'
        storage.mkdir(parents=True)
        (storage / 'source.md').write_text('Existing unrelated source')
        self.git('add', '.agentic-loop')
        self.git('commit', '-m', 'base run storage')
        self.git('branch', 'occupied-base')
        self.git('push', 'origin', 'occupied-base')
        self.git('rm', '-r', '.agentic-loop')
        self.git('commit', '-m', 'remove run storage')
        self.run_init('--issue', '42', '--base-ref', 'occupied-base', ok=False)
        self.assertEqual(self.git('branch', '--show-current'), 'main')
        self.assertFalse(storage.exists())
    def test_base_aliases_normalize_and_resume_equivalently(self):
        for number, alias in enumerate(['main', 'origin/main', 'refs/heads/main', 'refs/remotes/origin/main'], start=50):
            with self.subTest(alias=alias):
                result = self.run_init('--issue', str(number), '--base-ref', alias)
                self.assertEqual(result['base_ref'], 'main')
                for resume_alias in ['main', 'origin/main', 'refs/heads/main', 'refs/remotes/origin/main']:
                    self.assertTrue(self.run_init('--issue', str(number), '--base-ref', resume_alias)['resumed'])
                self.git('checkout', 'main')
    def test_commit_expressions_are_not_pr_base_branches(self):
        for base in [self.git('rev-parse', 'HEAD'), 'HEAD', 'main~0', 'main^{commit}', '--help', 'refs/tags/release']:
            with self.subTest(base=base):
                self.run_init('--base-ref', base, ok=False)
                self.assertEqual(self.git('branch', '--show-current'), 'main')
                self.assertFalse((self.repo / '.agentic-loop').exists())
    def test_remote_only_base_has_branchname_metadata(self):
        self.git('push', 'origin', 'main:refs/heads/release/x')
        self.git('fetch', 'origin', 'refs/heads/release/x:refs/remotes/origin/release/x')
        result = self.run_init('--base-ref', 'origin/release/x')
        self.assertEqual(result['base_ref'], 'release/x')
        self.assertTrue(self.run_init('--base-ref', 'refs/remotes/origin/release/x')['resumed'])
    def test_stale_remote_tracking_base_rejected(self):
        self.git('update-ref', 'refs/remotes/origin/stale', 'HEAD')
        self.run_init('--base-ref', 'origin/stale', ok=False)
        self.assertEqual(self.git('branch', '--show-current'), 'main')
        self.assertFalse((self.repo / '.agentic-loop').exists())
    def test_bad_identifiers(self):
        self.run_init('--issue', '../escape', ok=False)
        self.run_init('--run-id', '../escape', ok=False)
        self.assertFalse((self.repo / '.agentic-loop').exists())

    def test_local_only_base_rejected_before_mutation(self):
        self.git('branch', 'local-only')
        self.run_init('--base-ref', 'local-only', ok=False)
        self.assertEqual(self.git('branch', '--show-current'), 'main')
        self.assertFalse((self.repo / '.agentic-loop').exists())
        self.assertEqual(self.git('branch', '--list', 'feat/*'), '')

    def test_missing_origin_tracking_ref_requires_fetch(self):
        self.git('update-ref', '-d', 'refs/remotes/origin/main')
        error = self.run_init(ok=False)
        self.assertIn('fetch', error.lower())
        self.assertEqual(self.git('branch', '--show-current'), 'main')
        self.assertFalse((self.repo / '.agentic-loop').exists())

    def test_deleted_remote_base_refuses_resume_without_changes(self):
        self.git('branch', 'release')
        self.git('push', 'origin', 'release')
        result = self.run_init('--base-ref', 'release')
        run = self.repo / result['run_dir']
        (run / 'run-requirements.json').write_text('{"skills":["required"]}')
        before = {p.name: p.read_bytes() for p in run.iterdir()}
        self.git('push', 'origin', '--delete', 'release')
        self.run_init('--run-id', result['run_id'], ok=False)
        self.assertEqual(self.git('branch', '--show-current'), result['branch'])
        self.assertEqual(before, {p.name: p.read_bytes() for p in run.iterdir()})

if __name__ == '__main__':
    unittest.main()
