#!/usr/bin/env python3
"""Opt-in real Skills CLI installation eval; no unittest-discovered test cases."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-network', action='store_true', help='Allow pnpm dlx to resolve/run the Skills CLI')
    parser.add_argument('--evidence', type=Path, default=Path('/tmp/spec-to-pr-install-evidence.txt'))
    args = parser.parse_args()
    if not args.allow_network:
        parser.error('Explicit --allow-network is required; this eval invokes pnpm dlx')
    repo = Path(__file__).resolve().parents[2]
    names = ['agentic-loop', 'validating-specs', 'writing-documentation']
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
                raise RuntimeError(f'Command failed ({result.returncode}): {command}')
            return result.stdout

        run(['pnpm', 'dlx', 'skills', '--version'], root)
        listing = run(['pnpm', 'dlx', 'skills', 'add', str(source), '--list'], root)
        if 'Found 3 skills' not in listing:
            raise AssertionError('Expected exactly three discoverable skills')
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
            log.write(f'PASS {destination.name}: both harness destinations, exact closure after source removal\n')
        log.write('PASS 8 installs; counts ' + json.dumps({k: len(v) for k, v in snapshots.items()}) + '\n')
        print(f'PASS: 8 isolated installations; evidence {args.evidence}')


if __name__ == '__main__':
    main()
