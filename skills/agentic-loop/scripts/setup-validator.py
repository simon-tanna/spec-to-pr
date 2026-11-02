#!/usr/bin/env python3
"""Install the validator into a project's host directories when explicitly invoked."""
from __future__ import annotations  # keep older interpreters importing far enough to report the version

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

CLAUDE = '.claude/agents/spec-design-validator.md'
CODEX = '.codex/agents/spec-design-validator.toml'
REFERENCES = '.spec-to-pr/validator/references'
METADATA = '.spec-to-pr/validator/ownership.json'
ALLOWED = {CLAUDE, CODEX, REFERENCES + '/ledger.schema.json', REFERENCES + '/project-checks.md'}
PLACEHOLDER = '`{{PROJECT_REFERENCES}}`'


def digest(content: bytes) -> str:
    """Hash installed bytes for subsequent ownership checks."""
    return hashlib.sha256(content).hexdigest()


def substitute(source: Path, replacement: str) -> str:
    """Replace the single references placeholder, refusing a payload that lacks it."""
    text = source.read_text(encoding='utf-8')
    if text.count(PLACEHOLDER) != 1:
        raise ValueError(f'{source}: expected exactly one {PLACEHOLDER} placeholder')
    return text.replace(PLACEHOLDER, replacement)


def planned_files(skill_root: Path, project_root: Path, host: str) -> dict[Path, bytes]:
    """Render selected host payloads and their project-local reference closure.

    References come first so that an interrupted install never leaves a registered
    agent whose reference directory is missing.
    """
    native = skill_root / 'references/native-validator'
    planned = {}
    for name in ('ledger.schema.json', 'project-checks.md'):
        planned[project_root / REFERENCES / name] = (native / 'references' / name).read_bytes()
    reference_path = str(project_root / REFERENCES)
    # JSON-encode the path, then wrap it in a Markdown code span whose backtick fence
    # is longer than any backtick run inside the path.
    encoded = json.dumps(reference_path, ensure_ascii=False)
    delimiter = '`' * (max((len(run) for run in re.findall(r'`+', encoded)), default=0) + 1)
    span = delimiter + ' ' + encoded + ' ' + delimiter
    replacement = 'the directory specified by this JSON string: ' + span
    if host in ('claude', 'both'):
        planned[project_root / CLAUDE] = substitute(native / 'claude.md', replacement).encode('utf-8')
    if host in ('codex', 'both'):
        # The Codex payload embeds instructions in a TOML basic string: JSON escapes are
        # valid there, but TOML also requires DEL to be escaped.
        toml_text = json.dumps(replacement, ensure_ascii=False).replace('\x7f', '\\u007f')[1:-1]
        planned[project_root / CODEX] = substitute(native / 'codex.toml', toml_text).encode('utf-8')
    return planned


def safe_destination(project_root: Path, path: Path) -> None:
    """Reject symlinks and non-directory ancestors before inspecting any payload."""
    relative = path.relative_to(project_root)
    current = project_root
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise ValueError(f'{relative}: symlink destination or ancestor: {current}')
        if current != path and current.exists() and not current.is_dir():
            raise ValueError(f'{relative}: ancestor is not a directory: {current}')
    if path.exists() and not path.is_file():
        raise ValueError(f'{relative}: destination is not a regular file')


def ownership(project_root: Path) -> dict[str, str]:
    """Read only versioned, allowlisted ownership metadata with valid hashes."""
    path = project_root / METADATA
    safe_destination(project_root, path)
    if not path.exists():
        return {}
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, UnicodeError) as error:
        raise ValueError(f'{METADATA}: invalid ownership metadata: {error}') from error
    if (not isinstance(document, dict) or set(document) != {'version', 'files'}
            or type(document['version']) is not int or document['version'] != 1
            or not isinstance(document['files'], dict)):
        raise ValueError(f'{METADATA}: invalid ownership metadata')
    for name, value in document['files'].items():
        if name not in ALLOWED or not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
            raise ValueError(f'{METADATA}: unsafe ownership entry {name!r}')
    return document['files']


def preflight(project_root: Path, planned: dict[Path, bytes]) -> dict[str, str]:
    """Classify every destination and reject conflicts before any writes occur."""
    owned = ownership(project_root)
    statuses = {}
    errors = []
    for path, content in planned.items():
        relative = path.relative_to(project_root).as_posix()
        try:
            if relative not in ALLOWED:
                raise ValueError(f'{relative}: unexpected destination')
            safe_destination(project_root, path)
            if not path.exists():
                statuses[relative] = 'created'
            else:
                previous = path.read_bytes()
                if previous == content:
                    statuses[relative] = 'unchanged'
                elif owned.get(relative) == digest(previous):
                    statuses[relative] = 'updated'
                else:
                    raise ValueError(f'{relative}: conflicts with unmanaged content or local modifications')
        except (ValueError, OSError) as error:
            errors.append(str(error))
    if errors:
        raise ValueError('\n'.join(errors))
    return statuses


def write_atomic(path: Path, content: bytes) -> None:
    """Replace path with content in one step, so a failure never leaves a truncated file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # The temporary name keeps a non-host suffix so agent discovery never picks it up.
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.', suffix='.tmp')
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(content)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def install(project_root: Path, planned: dict[Path, bytes], statuses: dict[str, str], written: list[str]) -> None:
    """Write preflighted changes and record ownership last, retaining other hosts.

    Appends each completed managed path to written, for failure reporting.
    """
    owned = ownership(project_root)
    for path, content in planned.items():
        relative = path.relative_to(project_root).as_posix()
        if statuses[relative] != 'unchanged':
            write_atomic(path, content)
            written.append(relative)
        owned[relative] = digest(content)
    metadata = project_root / METADATA
    content = (json.dumps({'version': 1, 'files': owned}, indent=2, sort_keys=True) + '\n').encode('utf-8')
    if not metadata.exists() or metadata.read_bytes() != content:
        write_atomic(metadata, content)


def main(argv: list[str] | None = None) -> int:
    """Validate the selected project, install safely, and report host reload guidance."""
    if sys.version_info < (3, 10):
        found = '.'.join(str(part) for part in sys.version_info[:3])
        print(f'Validator setup failed: setup-validator.py requires Python 3.10+; found {found}.', file=sys.stderr)
        return 1
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, choices=('claude', 'codex', 'both'))
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    written: list[str] = []
    try:
        root = args.project_root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError(f'{root}: project root must be a directory')
        planned = planned_files(Path(__file__).resolve().parents[1], root, args.host)
        statuses = preflight(root, planned)
        install(root, planned, statuses, written)
    except (OSError, ValueError, UnicodeError) as error:
        print(f'Validator setup failed: {error}', file=sys.stderr)
        if written:
            print('Complete files written before the failure: ' + ', '.join(written) + '. Ownership is '
                  'recorded last, so fix the reported cause and rerun setup to finish.', file=sys.stderr)
        else:
            print('No files were written. Preserve local edits: reconcile, restore or remove each reported '
                  'path, then rerun setup.', file=sys.stderr)
        return 1
    print(f'Project root: {root}')
    for relative, status in statuses.items():
        print(f'{status}: {relative}')
    print('Reload the host or start a new session to discover registrations. Installation does not verify runtime discovery.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
