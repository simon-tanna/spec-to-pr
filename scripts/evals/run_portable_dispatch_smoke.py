#!/usr/bin/env python3
"""Live generic-child smoke test; does not establish interactive suite acceptance.

Uses existing authentication without editing user config. Raw traces remain local
in the requested output directory. Never treats a controller-only answer as PASS.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import uuid


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def evidence(events, harness, marker):
    nodes = [node for event in events for node in walk(event)]
    if harness == "claude":
        calls = [n for n in nodes if n.get("type") == "tool_use" and n.get("name") in ("Agent", "Task")]
        ids = {n.get("id") for n in calls}
        results = [n for n in nodes if n.get("type") == "tool_result" and n.get("tool_use_id") in ids and not n.get("is_error")]
        return bool(calls), any(marker in json.dumps(n.get("content", "")) for n in results)
    calls = [n for n in nodes if n.get("type") == "collab_tool_call" and n.get("tool") == "spawn_agent"]
    waits = [n for n in nodes if n.get("type") == "collab_tool_call" and n.get("tool") in ("wait", "wait_agent")]
    child_ids = {child for call in calls for child in call.get("receiver_thread_ids", [])}
    returned = any(
        child in child_ids and result.get("status") == "completed" and marker in result.get("message", "")
        for event in waits + calls for child, result in event.get("agents_states", event.get("agents", {})).items()
        if isinstance(result, dict)
    )
    return bool(calls), returned


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", choices=("codex", "claude"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error("timeout must be positive")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    version = subprocess.run([args.harness, "--version"], capture_output=True, text=True, timeout=10)
    with tempfile.TemporaryDirectory(prefix="portable-dispatch-") as scratch:
        root = Path(scratch)
        marker = "CHILD_RESULT_" + uuid.uuid4().hex
        (root / "fixture.txt").write_text(marker + "\n")
        prompt = (
            "Exercise actual child delegation. Spawn exactly one generic child with fresh context, "
            "supplying this role explicitly: read-only fixture reviewer; read fixture.txt in " + str(root) +
            "; return its exact first line. No recursive delegation. Wait for that child and report "
            "its returned line. You the controller must not read the fixture yourself or substitute "
            "an inline answer. Use the exposed native spawning tool, not a shell subprocess. "
            "If spawning or fresh context is unavailable, report BLOCKED and why. Do not edit files."
        )
        if args.harness == "codex":
            command = ["codex", "exec", "--ephemeral", "--ignore-user-config", "--sandbox", "read-only", "--json", "-C", scratch, "--skip-git-repo-check", prompt]
        else:
            command = ["claude", "-p", "--no-session-persistence", "--output-format", "stream-json", "--verbose", "--permission-mode", "dontAsk", "--allowedTools", "Read,Glob,Grep,Agent", "--tools", "Read,Glob,Grep,Agent", "--strict-mcp-config", "--setting-sources", "", "--", prompt]
        (out / "command.json").write_text(json.dumps(command, indent=2) + "\n")
        timed_out = False
        with (out / "transcript.jsonl").open("w") as stdout, (out / "stderr.log").open("w") as stderr:
            process = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                code = process.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    code = process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    code = process.wait()
        events = []
        for line in (out / "transcript.jsonl").read_text().splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        spawned, returned = evidence(events, args.harness, marker)
        result = {"harness": args.harness, "version": version.stdout.strip(), "exit_code": code, "timed_out": timed_out,
                  "actual_spawn_observed": spawned, "child_marker_result_observed": returned,
                  "status": "PASS" if code == 0 and spawned and returned else "INCOMPLETE",
                  "scope": "Generic delegation smoke only; fresh-context semantics require trace inspection; not full interactive workflow acceptance."}
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
