#!/usr/bin/env python3
"""Install the validator into an explicitly selected project's host directories."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

CLAUDE = '.claude/agents/spec-design-validator.md'
CODEX = '.codex/agents/spec-design-validator.toml'
REFERENCES = '.spec-to-pr/validator/references'
METADATA = '.spec-to-pr/validator/ownership.json'
ALLOWED = {CLAUDE, CODEX, REFERENCES + '/ledger.schema.json', REFERENCES + '/project-checks.md'}


def digest(content: bytes) -> str:
    """Hash installed bytes for subsequent ownership checks."""
    return hashlib.sha256(content).hexdigest()


def planned_files(skill_root: Path, project_root: Path, host: str) -> dict[Path, bytes]:
    """Render selected host payloads and their project-local reference closure."""
    native = skill_root / 'references/native-validator'
    reference_path = str(project_root / REFERENCES)
    # Encode the path before embedding it in either host's Markdown instructions.
    encoded = json.dumps(reference_path, ensure_ascii=False)
    delimiter = '`' * (max((len(run) for run in re.findall(r'`+', encoded)), default=0) + 1)
    span = delimiter + ' ' + encoded + ' ' + delimiter
    replacement = 'the directory specified by this JSON string: ' + span
    planned = {}
    if host in ('claude', 'both'):
        text = (native / 'claude.md').read_text(encoding='utf-8')
        text = text.replace('`{{PROJECT_REFERENCES}}`', replacement)
        planned[project_root / CLAUDE] = text.encode('utf-8')
    if host in ('codex', 'both'):
        encoded = json.dumps(replacement, ensure_ascii=False).replace('\x7f', '\\u007f')[1:-1]
        text = (native / 'codex.toml').read_text(encoding='utf-8').replace('`{{PROJECT_REFERENCES}}`', encoded)
        planned[project_root / CODEX] = text.encode('utf-8')
    for name in ('ledger.schema.json', 'project-checks.md'):
        planned[project_root / REFERENCES / name] = (native / 'references' / name).read_bytes()
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


def install(project_root: Path, planned: dict[Path, bytes], statuses: dict[str, str]) -> None:
    """Write preflighted changes and record ownership last, retaining other hosts."""
    owned = ownership(project_root)
    for path, content in planned.items():
        relative = path.relative_to(project_root).as_posix()
        if statuses[relative] != 'unchanged':
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        owned[relative] = digest(content)
    metadata = project_root / METADATA
    content = (json.dumps({'version': 1, 'files': owned}, indent=2, sort_keys=True) + '\n').encode('utf-8')
    if not metadata.exists() or metadata.read_bytes() != content:
        metadata.parent.mkdir(parents=True, exist_ok=True)
        metadata.write_bytes(content)


def main(argv: list[str] | None = None) -> int:
    """Validate the selected project, install safely, and report host reload guidance."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, choices=('claude', 'codex', 'both'))
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        root = args.project_root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError(f'{root}: project root must be a directory')
        planned = planned_files(Path(__file__).resolve().parents[1], root, args.host)
        statuses = preflight(root, planned)
        install(root, planned, statuses)
    except (OSError, ValueError, UnicodeError) as error:
        print(f'Validator setup failed: {error}', file=sys.stderr)
        print('Preserve local edits and inspect the reported paths. After an I/O failure, partial managed files may remain; explicitly restore or remove affected partial managed files before retry. Rerun setup to recover missing or identical files.', file=sys.stderr)
        return 1
    for relative, status in statuses.items():
        print(f'{status}: {relative}')
    print('Reload the host or start a new session to discover registrations. Installation does not verify runtime discovery.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
