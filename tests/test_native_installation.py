"""Offline installation fixtures; real Skills CLI evidence is opt-in separately."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ('spec-design-validator', 'validating-specs', 'agentic-loop')


class NativeInstallationTests(unittest.TestCase):
    def test_independent_setup_after_source_removal(self):
        for name in SKILLS:
            for layout in ('.agents/skills', '.claude/skills'):
                with self.subTest(skill=name, layout=layout), tempfile.TemporaryDirectory() as tmp:
                    base = Path(tmp).resolve()
                    source = base / 'source'
                    shutil.copytree(ROOT / 'skills' / name, source)
                    installed = base / 'installed' / layout / name
                    shutil.copytree(source, installed)
                    shutil.rmtree(source)
                    for host in ('claude', 'codex', 'both'):
                        project = base / host
                        project.mkdir()
                        result = subprocess.run([sys.executable, str(installed / 'scripts/setup-validator.py'),
                                                 '--host', host], cwd=project, capture_output=True, text=True)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        refs = project / '.spec-to-pr/validator/references'
                        for reference in ('ledger.schema.json', 'project-checks.md'):
                            self.assertEqual((refs / reference).read_bytes(),
                                             (installed / 'references/native-validator/references' / reference).read_bytes())
                        if host != 'codex':
                            claude = (project / '.claude/agents/spec-design-validator.md').read_text()
                            self.assertTrue(claude.startswith('---\n'))
                            self.assertEqual(json.loads(re.search(r'^name: (.+)$', claude, re.M).group(1)), 'spec-design-validator')
                            self.assertIn(json.dumps(str(refs)), claude)
                        if host != 'claude':
                            codex = tomllib.loads((project / '.codex/agents/spec-design-validator.toml').read_text())
                            self.assertEqual(set(codex), {'name', 'description', 'developer_instructions'})
                            self.assertEqual(codex['name'], 'spec-design-validator')
                            self.assertIn(json.dumps(str(refs)), codex['developer_instructions'])

    def test_bundled_workflow_setup_paths_resolve_from_installed_root(self):
        for name, workflow_path in (
                ('validating-specs', 'SKILL.md'),
                ('agentic-loop', 'references/validation/workflow.md')):
            root = ROOT / 'skills' / name
            text = (root / workflow_path).read_text()
            self.assertIn('relative to that installed skill root', text)
            for relative in ('setup/SETUP.md', 'scripts/setup-validator.py'):
                self.assertIn(f'`{relative}`', text)
                self.assertTrue((root / relative).is_file())
            self.assertIn('explicit user setup step, separate from this', text)

    def test_real_evaluator_checks_installed_setup(self):
        spec = importlib.util.spec_from_file_location('install_eval', ROOT / 'scripts/evals/test_skills_install.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            installed = base / 'installed'
            shutil.copytree(ROOT / 'skills/spec-design-validator', installed)
            calls = []
            def run(command, cwd):
                calls.append(command)
                result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            module.verify_native_setup(installed, base / 'projects', run)
            self.assertEqual({call[call.index('--host') + 1] for call in calls}, {'claude', 'codex', 'both'})

    def test_documented_commands_match_cli(self):
        # These are literal runnable commands, not interface-shaped placeholders.
        commands = []
        for name in SKILLS:
            doc = (ROOT / 'skills' / name / 'setup/SETUP.md').read_text()
            examples = re.findall(r'^python3 "\$SKILL/scripts/setup-validator.py" --host (claude|codex|both)( --project-root "\$PROJECT")?$', doc, re.M)
            self.assertEqual({host for host, _ in examples}, {'claude', 'codex', 'both'}, name)
            self.assertIn('Python 3.10+', doc)
            commands.extend((name, host, bool(explicit)) for host, explicit in examples)
        for name, host, explicit in commands:
            with self.subTest(skill=name, host=host), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp)
                command = f'python3 "$SKILL/scripts/setup-validator.py" --host {host}'
                if explicit:
                    command += ' --project-root "$PROJECT"'
                environment = dict(os.environ, SKILL=str(ROOT / 'skills' / name), PROJECT=str(project))
                result = subprocess.run(['bash', '-c', command], cwd=project, env=environment,
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((project / '.claude/agents/spec-design-validator.md').exists(), host != 'codex')
                self.assertEqual((project / '.codex/agents/spec-design-validator.toml').exists(), host != 'claude')
        setup = (ROOT / 'skills/spec-design-validator/setup/SETUP.md').read_text().lower()
        for topic in ('conflict', 'ownership', 'upgrade', 'move', 'partial', 'reload', 'plugin', 'permissions', 'selector', 'fallback'):
            self.assertIn(topic, setup)
        rubric = (ROOT / 'skills/spec-design-validator/SKILL.md').read_text()
        self.assertNotIn('setup-validator.py', rubric)
        self.assertFalse((ROOT / 'skills/spec-design-validator/references/native-setup.md').exists())


if __name__ == '__main__':
    unittest.main()
