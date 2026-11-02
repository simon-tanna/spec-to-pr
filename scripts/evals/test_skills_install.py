#!/usr/bin/env python3
"""Opt-in real Skills CLI installation eval; no unittest-discovered test cases."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import sys
import tomllib


def verify_native_setup(installed, projects, run):
    """Execute the installed command and validate selected host/reference closure."""
    for host in ('claude', 'codex', 'both'):
        project = (projects / host).resolve()
        project.mkdir(parents=True)
        run([sys.executable, str(installed / 'scripts/setup-validator.py'),
             '--host', host, '--project-root', str(project)], project)
        references = project / '.spec-to-pr/validator/references'
        for name in ('ledger.schema.json', 'project-checks.md'):
            if (references / name).read_bytes() != (installed / 'references/native-validator/references' / name).read_bytes():
                raise AssertionError(f'Changed native reference: {references / name}')
        json.loads((references / 'ledger.schema.json').read_text())
        claude = project / '.claude/agents/spec-design-validator.md'
        codex = project / '.codex/agents/spec-design-validator.toml'
        if claude.exists() != (host != 'codex') or codex.exists() != (host != 'claude'):
            raise AssertionError(f'Unexpected host destinations: {project}')
        bodies = []
        if claude.exists():
            text = claude.read_text()
            # Generated YAML uses JSON-quoted scalars, a strict YAML subset.
            header, body = text.removeprefix('---\n').split('\n---\n', 1)
            fields = dict(line.split(': ', 1) for line in header.splitlines())
            if json.loads(fields['name']) != 'spec-design-validator':
                raise AssertionError(f'Invalid Claude agent name: {claude}')
            for key in ('name', 'description'):
                if not isinstance(json.loads(fields[key]), str):
                    raise AssertionError(f'Invalid Claude scalar: {key}')
            if fields['model'] != 'opus' or fields['disallowedTools'] != 'Write, Edit, NotebookEdit, Agent':
                raise AssertionError(f'Changed Claude host contract: {claude}')
            bodies.append(body)
        if codex.exists():
            fields = tomllib.loads(codex.read_text())
            if set(fields) != {'name', 'description', 'developer_instructions'} or fields['name'] != 'spec-design-validator':
                raise AssertionError(f'Invalid Codex agent schema: {codex}')
            if not all(isinstance(value, str) for value in fields.values()):
                raise AssertionError(f'Invalid Codex agent fields: {codex}')
            bodies.append(fields['developer_instructions'])
        for body in bodies:
            if json.dumps(str(references), ensure_ascii=False) not in body or '{{PROJECT_REFERENCES}}' in body or 'CLAUDE_PLUGIN_ROOT' in body:
                raise AssertionError(f'Unresolved native reference closure: {project}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-network', action='store_true', help='Allow pnpm dlx to resolve/run the Skills CLI')
    parser.add_argument('--evidence', type=Path, default=Path('/tmp/spec-to-pr-install-evidence.txt'))
    args = parser.parse_args()
    if not args.allow_network:
        parser.error('Explicit --allow-network is required; this eval invokes pnpm dlx')
    repo = Path(__file__).resolve().parents[2]
    names = ['agentic-loop', 'validating-specs', 'diataxis-docs', 'spec-design-validator']
    with tempfile.TemporaryDirectory(prefix='spec-to-pr-install-') as tmp, args.evidence.open('a') as log:
        root = Path(tmp)
        source = root / 'source'
        for name in names:
            shutil.copytree(repo / 'skills' / name, source / 'skills' / name,
                            ignore=shutil.ignore_patterns('__pycache__'))
        # Include the optional plugin layout so discovery matches the published
        # repository; skills-only fixtures could hide manifest discovery bugs.
        for directory in ['.claude-plugin', 'agents', 'hooks']:
            shutil.copytree(repo / directory, source / directory, ignore=shutil.ignore_patterns('__pycache__'))
        snapshots = {name: {p.relative_to(source / 'skills' / name): p.read_bytes()
                           for p in (source / 'skills' / name).rglob('*') if p.is_file()} for name in names}

        def run(command, cwd):
            result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
            log.write(json.dumps(command) + '\n' + result.stdout + result.stderr + '\n')
            log.flush()
            if result.returncode:
                raise RuntimeError(f'Command failed ({result.returncode}): {command}; '
                                   f'output in {args.evidence}\n{result.stderr[-2000:]}')
            return result.stdout

        run(['pnpm', 'dlx', 'skills', '--version'], root)
        listing = run(['pnpm', 'dlx', 'skills', 'add', str(source), '--list'], root)
        if not re.search(r'\bFound 4 skills\b', listing):
            raise AssertionError(f'Expected exactly four discoverable skills; listing:\n{listing}')
        installations = []
        for mode in ['default', 'copy']:
            for selected in [['*'], *[[name] for name in names]]:
                destination = root / (mode + '-' + selected[0].replace('*', 'suite'))
                destination.mkdir()
                command = ['pnpm', 'dlx', 'skills', 'add', str(source), '--skill', *selected,
                           '-a', 'codex', '-a', 'claude-code', '-y']
                if mode == 'copy':
                    command.append('--copy')
                run(command, destination)
                expected = names if selected == ['*'] else selected
                installations.append((destination, expected))
        shutil.rmtree(source)
        # Verify every file only after source removal; installing siblings cannot
        # mask closure in the three single-skill cases.
        for destination, expected in installations:
            for prefix in ['.agents/skills', '.claude/skills']:
                discovered = {p.parent.name for p in (destination / prefix).glob('*/SKILL.md')}
                if discovered != set(expected):
                    raise AssertionError(f'Unexpected entrypoints: {destination / prefix}: {discovered}')
                for name in expected:
                    for relative, content in snapshots[name].items():
                        installed = destination / prefix / name / relative
                        if not installed.is_file() or installed.read_bytes() != content:
                            raise AssertionError(f'Missing or changed installed asset: {installed}')
                    if name in ('spec-design-validator', 'validating-specs', 'agentic-loop'):
                        projects = destination / 'native-setup-eval' / prefix.split('/')[0] / name
                        verify_native_setup(destination / prefix / name, projects, run)
                        log.write(f'PASS {destination.name} {prefix}/{name}: all selected hosts, native syntax and reference closure after source removal\n')
            log.write(f'PASS {destination.name}: both harness destinations, exact closure after source removal\n')
        log.write(f'PASS {len(installations)} installs; counts ' + json.dumps({k: len(v) for k, v in snapshots.items()}) + '\n')
        print(f'PASS: {len(installations)} isolated installations; evidence {args.evidence}')


if __name__ == '__main__':
    main()
