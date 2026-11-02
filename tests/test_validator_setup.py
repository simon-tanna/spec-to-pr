"""Exercise the independently shipped project validator installer."""
import ast
import contextlib
import importlib.util
import io
import json
import os
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
REFERENCES = ('.spec-to-pr/validator/references/ledger.schema.json',
              '.spec-to-pr/validator/references/project-checks.md')


def older_interpreter():
    """Locate a pre-3.10 interpreter on this machine, if any, for the version-guard check."""
    for candidate in ('python3.9', 'python3.8', '/usr/bin/python3'):
        path = shutil.which(candidate) or (candidate if Path(candidate).is_file() else None)
        if not path:
            continue
        probe = subprocess.run([path, '-c', 'import sys; print(sys.version_info < (3, 10))'],
                               capture_output=True, text=True)
        if probe.returncode == 0 and probe.stdout.strip() == 'True':
            return path
    return None


OLDER_PYTHON = older_interpreter()


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

    def load_module(self, script=None):
        spec = importlib.util.spec_from_file_location('validator_setup', script or self.script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def run_main(self, module, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = module.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def installed_copy(self, name='installed'):
        installed = self.base / name
        shutil.copytree(ROOT / 'skills/spec-design-validator', installed)
        return installed

    def upgraded_copy(self, name='upgraded'):
        """An installed skill whose every managed payload differs from the shipped one."""
        installed = self.installed_copy(name)
        native = installed / 'references/native-validator'
        for relative in ('claude.md', 'codex.toml', 'references/project-checks.md'):
            path = native / relative
            path.write_text(path.read_text() + '\n# Upgrade sentinel.\n')
        return installed / 'scripts/setup-validator.py'

    def test_required_host_and_project_selection(self):
        for host, root in ((None, None), ('invalid', None), ('both', self.base / 'absent')):
            self.assertNotEqual(self.run_setup(host=host, root=root).returncode, 0)
            self.assertEqual(self.snapshot(), {})
        for host in ('claude', 'codex', 'both'):
            project = self.base / host
            project.mkdir()
            self.assertIn(f'Project root: {project}', self.success(host=host, root=project).stdout)
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
            for host in ('claude', 'codex', 'both'):
                with self.subTest(skill=skill, host=host):
                    project = self.base / (str(index) + host + ' space "quote" \\ café 東京 🐈 `tick` \x7f\n## path-heading')
                    project.mkdir()
                    self.success(host=host, root=project, script=installed / 'scripts/setup-validator.py')
                    reference = str(project / '.spec-to-pr/validator/references')
                    contents = []
                    self.assertEqual((project / CLAUDE).exists(), host != 'codex')
                    self.assertEqual((project / CODEX).exists(), host != 'claude')
                    if host != 'codex':
                        claude = (project / CLAUDE).read_text()
                        self.assertIn(json.dumps(reference, ensure_ascii=False), claude)
                        self.assertNotIn(reference, claude)
                        contents.append(claude)
                    if host != 'claude':
                        codex = tomllib.loads((project / CODEX).read_text())
                        self.assertIn(json.dumps(reference, ensure_ascii=False), codex['developer_instructions'])
                        self.assertNotIn(reference, codex['developer_instructions'])
                        self.assertNotIn('\n## path-heading', codex['developer_instructions'])
                        self.assertEqual(set(codex), {'name', 'description', 'developer_instructions'})
                        contents.append(codex['developer_instructions'])
                    for content in contents:
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
            before = self.snapshot()
            result = self.run_setup()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(relative, result.stderr)
            self.assertEqual(before, self.snapshot())
            self.assertTrue(path.is_dir())
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
        agent = self.project / '.codex/agents/local-agent.toml'
        agent.parent.mkdir()
        agent_bytes = b'name = \"local-agent\"\n# local instructions\n'
        agent.write_bytes(agent_bytes)
        self.assertTrue(self.script.is_file(), str(self.script))
        module = self.load_module()
        real_replace = os.replace
        def fail_metadata(source, destination):
            if Path(destination).name == 'ownership.json':
                raise OSError('injected write failure')
            return real_replace(source, destination)
        with patch.object(os, 'replace', fail_metadata):
            result, stdout, stderr = self.run_main(module, ['--host', 'both', '--project-root', str(self.project)])
        self.assertNotEqual(result, 0)
        for word in ('created', 'updated', 'unchanged', 'reload'):
            self.assertNotIn(word, stdout.lower())
        self.assertEqual(agent.read_bytes(), agent_bytes)
        self.assertIn('injected write failure', stderr)
        for relative in (CLAUDE, CODEX, *REFERENCES):
            self.assertIn(relative, stderr)
        self.assertIn('rerun', stderr.lower())
        result = self.success()
        self.assertIn('session', result.stdout.lower())
        self.assertIn('reload', result.stdout.lower())
        self.assertEqual(unrelated.read_text(), 'unrelated = true\n')
        self.assertEqual(agent.read_bytes(), agent_bytes)

    def test_interrupted_install_never_registers_without_references(self):
        module = self.load_module()
        real_replace = os.replace
        planned = module.planned_files(self.script.resolve().parents[1], self.project, 'both')
        for failing in range(1, len(planned) + 2):  # every managed file, then the manifest
            with self.subTest(failing=failing):
                project = self.base / f'interrupted-{failing}'
                project.mkdir()
                calls = []
                def replace(source, destination):
                    calls.append(destination)
                    if len(calls) == failing:
                        raise OSError('injected replace failure')
                    return real_replace(source, destination)
                with patch.object(os, 'replace', replace):
                    code, stdout, stderr = self.run_main(module, ['--host', 'both', '--project-root', str(project)])
                self.assertEqual(code, 1)
                self.assertIn('injected replace failure', stderr)
                files = {p.relative_to(project).as_posix() for p in project.rglob('*') if p.is_file()}
                self.assertEqual([f for f in files if f.endswith('.tmp')], [])
                self.assertNotIn(MANIFEST, files)
                if CLAUDE in files or CODEX in files:
                    self.assertTrue(set(REFERENCES) <= files, files)
                expected = module.planned_files(self.script.resolve().parents[1], project, 'both')
                for path, content in expected.items():
                    relative = path.relative_to(project).as_posix()
                    if relative in files:
                        self.assertEqual(path.read_bytes(), content)  # complete, never truncated
                        self.assertIn(relative, stderr)
                if not files:
                    self.assertIn('No files were written', stderr)
                self.success(root=project)
                self.assertTrue((project / MANIFEST).is_file())

    def test_interrupted_upgrade_recovers_on_rerun(self):
        self.success()
        script = self.upgraded_copy()
        module = self.load_module(script)
        real_replace = os.replace
        calls = []
        def replace(source, destination):
            calls.append(destination)
            if len(calls) == 2:
                raise OSError('injected replace failure')
            return real_replace(source, destination)
        with patch.object(os, 'replace', replace):
            code, _, _ = self.run_main(module, ['--host', 'both', '--project-root', str(self.project)])
        self.assertEqual(code, 1)
        self.success(script=script)
        for relative in (CLAUDE, CODEX, REFERENCES[1]):
            self.assertIn('Upgrade sentinel.', (self.project / relative).read_text())

    def test_upgrade_preserves_local_edit_as_conflict(self):
        self.success()
        (self.project / CLAUDE).write_bytes(b'local edits')
        before = self.snapshot()
        result = self.run_setup(script=self.upgraded_copy())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(CLAUDE, result.stderr)
        self.assertIn('No files were written', result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_single_host_ignores_other_hosts_unmanaged_file(self):
        for host, other in (('claude', CODEX), ('codex', CLAUDE)):
            with self.subTest(host=host):
                project = self.base / ('isolated-' + host)
                foreign = project / other
                foreign.parent.mkdir(parents=True)
                foreign.write_bytes(b'foreign agent')
                self.success(host=host, root=project)
                self.assertEqual(foreign.read_bytes(), b'foreign agent')
                manifest = json.loads((project / MANIFEST).read_text())
                self.assertNotIn(other, manifest['files'])

    def test_missing_placeholder_fails_before_writes(self):
        for host, name in (('claude', 'claude.md'), ('codex', 'codex.toml')):
            with self.subTest(host=host):
                installed = self.installed_copy('placeholder-' + host)
                payload = installed / 'references/native-validator' / name
                payload.write_text(payload.read_text().replace('`{{PROJECT_REFERENCES}}`', '`elsewhere`'))
                result = self.run_setup(host=host, script=installed / 'scripts/setup-validator.py')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('{{PROJECT_REFERENCES}}', result.stderr)
                self.assertEqual(self.snapshot(), {})

    def test_annotations_are_not_evaluated_on_older_interpreters(self):
        tree = ast.parse(self.script.read_text())
        future = tree.body[1]
        self.assertIsInstance(future, ast.ImportFrom)
        self.assertEqual((future.module, [alias.name for alias in future.names]), ('__future__', ['annotations']))
        module = self.load_module()
        with patch.object(sys, 'version_info', (3, 9, 6, 'final', 0)):
            code, _, stderr = self.run_main(module, ['--host', 'both', '--project-root', str(self.project)])
        self.assertEqual(code, 1)
        self.assertIn('requires Python 3.10+', stderr)
        self.assertIn('3.9', stderr)
        self.assertEqual(self.snapshot(), {})

    @unittest.skipUnless(OLDER_PYTHON, 'no pre-3.10 interpreter available')
    def test_older_interpreter_reports_version_without_traceback(self):
        result = subprocess.run([OLDER_PYTHON, str(self.script), '--host', 'both', '--project-root', str(self.project)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('requires Python 3.10+', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(self.snapshot(), {})


if __name__ == '__main__':
    unittest.main()
