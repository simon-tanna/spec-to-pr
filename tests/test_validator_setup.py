"""Exercise the independently shipped project validator installer."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ('spec-design-validator', 'validating-specs', 'agentic-loop')
MANIFEST = '.spec-to-pr/validator/ownership.json'
CLAUDE = '.claude/agents/spec-design-validator.md'
CODEX = '.codex/agents/spec-design-validator.toml'


class ValidatorSetupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.project = self.base / 'project'
        self.project.mkdir()
        self.script = ROOT / 'skills/spec-design-validator/scripts/setup-validator.py'

    def run_setup(self, host='both', root=None, script=None, extra=()):
        return subprocess.run([sys.executable, str(script or self.script),
                               *(['--host', host] if host else []),
                               *(['--project-root', str(root)] if root else []), *extra],
                              cwd=self.project, text=True, capture_output=True)

    def success(self, **kwargs):
        result = self.run_setup(**kwargs)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def snapshot(self):
        return {str(p.relative_to(self.project)): p.read_bytes()
                for p in self.project.rglob('*') if p.is_file()}

    def test_required_host_and_project_selection(self):
        for host, root in ((None, None), ('invalid', None), ('both', self.base / 'absent')):
            self.assertNotEqual(self.run_setup(host=host, root=root).returncode, 0)
            self.assertEqual(self.snapshot(), {})
        for host in ('claude', 'codex', 'both'):
            project = self.base / host
            project.mkdir()
            self.success(host=host, root=project)
            self.assertEqual((project / CLAUDE).exists(), host != 'codex')
            self.assertEqual((project / CODEX).exists(), host != 'claude')
        self.success()
        self.assertTrue((self.project / MANIFEST).exists())

    def test_self_contained_resources_and_escaped_paths(self):
        for index, skill in enumerate(SKILLS):
            installed = self.base / ('installed' + str(index))
            shutil.copytree(ROOT / 'skills' / skill / 'references/native-validator', installed / 'references/native-validator')
            (installed / 'scripts').mkdir()
            shutil.copy2(ROOT / 'skills' / skill / 'scripts/setup-validator.py', installed / 'scripts/setup-validator.py')
            project = self.base / (str(index) + ' space "quote" \\ café 東京 🐈 `tick` \x7f\nnext line')
            project.mkdir()
            self.success(root=project, script=installed / 'scripts/setup-validator.py')
            reference = str(project / '.spec-to-pr/validator/references')
            claude = (project / CLAUDE).read_text()
            codex = tomllib.loads((project / CODEX).read_text())
            self.assertIn(json.dumps(reference, ensure_ascii=False), claude)
            self.assertNotIn(reference, claude)
            self.assertIn(reference, codex['developer_instructions'])
            self.assertEqual(set(codex), {'name', 'description', 'developer_instructions'})
            for content in (claude, codex['developer_instructions']):
                self.assertNotIn('{{PROJECT_REFERENCES}}', content)
                self.assertNotIn('CLAUDE_PLUGIN_ROOT', content)
            self.assertTrue((Path(reference) / 'ledger.schema.json').is_file())
            self.assertTrue((Path(reference) / 'project-checks.md').is_file())

    def test_repeat_update_and_move(self):
        first = self.success(host='claude')
        self.assertIn('created', first.stdout)
        before = {p: p.stat().st_mtime_ns for p in self.project.rglob('*') if p.is_file()}
        self.assertIn('unchanged', self.success(host='claude').stdout)
        self.assertEqual(before, {p: p.stat().st_mtime_ns for p in before})
        self.success()
        self.success(host='codex')
        manifest = json.loads((self.project / MANIFEST).read_text())
        self.assertIn(CLAUDE, manifest['files'])
        self.assertIn(CODEX, manifest['files'])
        installed = self.base / 'installed'
        shutil.copytree(ROOT / 'skills/spec-design-validator', installed)
        payload = installed / 'references/native-validator/claude.md'
        payload.write_text(payload.read_text() + '\nUpgrade sentinel.\n')
        self.assertIn('updated', self.success(script=installed / 'scripts/setup-validator.py').stdout)
        self.assertIn('Upgrade sentinel.', (self.project / CLAUDE).read_text())
        moved = self.base / 'moved'
        self.project.rename(moved)
        self.project = moved
        self.assertIn('updated', self.success(script=installed / 'scripts/setup-validator.py').stdout)
        self.assertIn(str(moved), (moved / CLAUDE).read_text())

    def test_conflicts_preflight_every_destination(self):
        collision = self.project / CODEX
        collision.parent.mkdir(parents=True)
        collision.write_bytes(b'unmanaged conflict')
        before = self.snapshot()
        result = self.run_setup()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(CODEX, result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.project / '.claude').exists())
        collision.unlink()
        self.success()
        original = self.snapshot()
        for relative in original:
            if relative == MANIFEST:
                continue
            path = self.project / relative
            path.write_bytes(b'local edits')
            before = self.snapshot()
            result = self.run_setup()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(relative, result.stderr)
            self.assertEqual(before, self.snapshot())
            path.unlink()
            path.mkdir()
            result = self.run_setup()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(relative, result.stderr)
            path.rmdir()
            path.write_bytes(original[relative])
        (self.project / MANIFEST).unlink()
        self.success()  # Identical unmanaged payloads may be adopted.
        self.assertTrue((self.project / MANIFEST).exists())

    def test_reject_symlink_escape_and_unsafe_metadata(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (self.project / '.claude').symlink_to(outside, target_is_directory=True)
        self.assertNotEqual(self.run_setup().returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])
        (self.project / '.claude').unlink()
        self.success()
        manifest = self.project / MANIFEST
        original = manifest.read_bytes()
        for content in ('not json', '{}', json.dumps({'version': 1, 'files': {'../escape': 'a'*64}}),
                        json.dumps({'version': 1, 'files': {'/absolute': 'a'*64}}),
                        json.dumps({'version': 1, 'files': {CLAUDE: 'wrong'}}),
                        json.dumps({'version': 1, 'files': {'unrelated.txt': 'a'*64}})):
            manifest.write_text(content)
            before = self.snapshot()
            self.assertNotEqual(self.run_setup().returncode, 0)
            self.assertEqual(before, self.snapshot())
        manifest.write_bytes(original)
        destination = self.project / CODEX
        destination.unlink()
        destination.symlink_to(outside / 'agent')
        self.assertNotEqual(self.run_setup().returncode, 0)
        self.assertFalse((outside / 'agent').exists())

    def test_unrelated_files_and_io_failure(self):
        unrelated = self.project / '.codex/config.toml'
        unrelated.parent.mkdir()
        unrelated.write_text('unrelated = true\n')
        self.assertTrue(self.script.is_file(), str(self.script))
        spec = importlib.util.spec_from_file_location('validator_setup', self.script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        real_write = Path.write_bytes
        def fail_metadata(path, content):
            if path.name == 'ownership.json':
                raise OSError('injected write failure')
            return real_write(path, content)
        import contextlib
        import io
        output = io.StringIO()
        with patch.object(Path, 'write_bytes', fail_metadata), contextlib.redirect_stderr(output):
            result = module.main(['--host', 'both', '--project-root', str(self.project)])
        self.assertNotEqual(result, 0)
        self.assertIn('injected write failure', output.getvalue())
        for word in ('preserve', 'inspect', 'restore', 'remove', 'retry'):
            self.assertIn(word, output.getvalue().lower())
        result = self.success()
        self.assertIn('session', result.stdout.lower())
        self.assertIn('reload', result.stdout.lower())
        self.assertEqual(unrelated.read_text(), 'unrelated = true\n')


if __name__ == '__main__':
    unittest.main()
