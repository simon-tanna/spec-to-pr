#!/usr/bin/env python3
"""Live generic-child smoke test; does not establish interactive suite acceptance.

Uses existing authentication without editing user config. Raw traces remain local
in the requested output directory. Never treats a controller-only answer as PASS.
Codex sessions persist so V2 child evidence can be read from this run's rollout.
"""
import argparse
import json
import os
from pathlib import Path
import re
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


def codex_rollout_evidence(records, marker):
    """Read native V2 response envelopes, never recursively mine quoted data."""
    items = [r.get("payload") for r in records if isinstance(r, dict) and r.get("type") == "response_item"]
    items = [item for item in items if isinstance(item, dict)]
    calls = [(i, item) for i, item in enumerate(items)
             if item.get("type") == "function_call" and item.get("namespace") == "collaboration"
             and item.get("name") == "spawn_agent"]
    if len(calls) != 1:
        return False, False
    index, call = calls[0]
    try:
        args = json.loads(call.get("arguments", ""))
    except (ValueError, TypeError):
        return False, False
    if not isinstance(args, dict) or args.get("fork_turns") != "none" or not call.get("call_id"):
        return False, False
    outputs = [(i, item) for i, item in enumerate(items) if item.get("type") == "function_call_output"
               and item.get("call_id") == call["call_id"]]
    if len(outputs) != 1 or outputs[0][0] <= index:
        return False, False
    output_index, output = outputs[0]
    try:
        result = json.loads(output.get("output", ""))
    except (ValueError, TypeError):
        return False, False
    if (not isinstance(result, dict) or result.get("error") or result.get("success") is False
            or output.get("is_error") or output.get("success") is False):
        return False, False
    child = result.get("task_name")
    if not isinstance(child, str) or not re.fullmatch(r"/(?:[A-Za-z0-9_-]+/)+[A-Za-z0-9_-]+", child):
        return False, False
    if child.rsplit("/", 1)[1] != args.get("task_name"):
        return False, False
    parent = child.rsplit("/", 1)[0]
    for item in items[output_index + 1:]:
        if item.get("type") != "agent_message" or item.get("author") != child or item.get("recipient") != parent:
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "input_text":
                continue
            text = block.get("text")
            if not isinstance(text, str):
                continue
            header, separator, payload = text.partition("\nPayload:\n")
            expected_header = f"Message Type: FINAL_ANSWER\nTask name: {parent}\nSender: {child}"
            if separator and header == expected_header and payload.strip() == marker:
                return True, True
    return True, False


def collect_codex_rollout(thread_id, scratch, snapshot, codex_home=None):
    """Snapshot only this exec session, rejecting missing or ambiguous evidence."""
    snapshot.unlink(missing_ok=True)
    if not isinstance(thread_id, str) or not re.fullmatch(r"[A-Za-z0-9-]+", thread_id):
        raise ValueError("Missing or invalid Codex controller thread ID")
    home = Path(codex_home if codex_home is not None else os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
    sessions = (home / "sessions").resolve()
    try:
        paths = list(sessions.rglob(f"rollout-*-{thread_id}.jsonl"))
        if len(paths) != 1:
            raise ValueError("Expected exactly one matching uncompressed Codex session record")
        path = paths[0]
        if path.is_symlink() or not path.resolve().is_relative_to(sessions):
            raise ValueError("Codex session record resolves outside the session directory")
        # A binary first-line read avoids decoding buffered bytes from a record
        # that belongs to another session. Do not consume its body until matched.
        with path.open("rb") as record:
            header = record.readline()
            first = json.loads(header)
            meta = first.get("payload") if isinstance(first, dict) else None
            if (not isinstance(first, dict) or first.get("type") != "session_meta"
                    or not isinstance(meta, dict) or meta.get("id") != thread_id
                    or meta.get("source") != "exec" or not isinstance(meta.get("cwd"), str)
                    or Path(meta["cwd"]).resolve() != Path(scratch).resolve()):
                raise ValueError("Codex session metadata does not match this controller and fixture directory")
            text = (header + record.read()).decode("utf-8")
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
        if not records or not all(isinstance(record, dict) for record in records):
            raise ValueError("Invalid Codex session record envelopes")
        snapshot.write_text(text)
        return records
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot collect Codex session evidence: {error}") from error


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
    snapshot = out / "codex-rollout.jsonl"
    snapshot.unlink(missing_ok=True)
    (out / "result.json").unlink(missing_ok=True)
    version = subprocess.run([args.harness, "--version"], capture_output=True, text=True, timeout=10)
    with tempfile.TemporaryDirectory(prefix="portable-dispatch-") as scratch:
        root = Path(scratch)
        marker = "CHILD_RESULT_" + uuid.uuid4().hex
        (root / "fixture.txt").write_text(marker + "\n")
        (out / "expected_marker.txt").write_text(marker + "\n")
        prompt = (
            "Exercise actual child delegation. Spawn exactly one generic child with fresh context, "
            "supplying this role explicitly: read-only fixture reviewer; read fixture.txt in " + str(root) +
            "; return its exact first line. No recursive delegation. Wait for that child and report "
            "its returned line. You the controller must not read the fixture yourself or substitute "
            "an inline answer. Use the exposed native spawning tool, not a shell subprocess. "
            "If spawning or fresh context is unavailable, report BLOCKED and why. Do not edit files."
        )
        if args.harness == "codex":
            command = ["codex", "exec", "--ignore-user-config", "--disable", "plugins", "--enable", "skip_host_skill_discovery", "--sandbox", "read-only", "--json", "-C", scratch, "--skip-git-repo-check", prompt]
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
        source = "jsonl"
        reasons = []
        if args.harness == "codex" and not (spawned and returned):
            thread_ids = {e.get("thread_id") for e in events
                          if isinstance(e, dict) and e.get("type") == "thread.started"
                          and isinstance(e.get("thread_id"), str)}
            thread_id = next(iter(thread_ids)) if len(thread_ids) == 1 else None
            try:
                records = collect_codex_rollout(thread_id, root, snapshot)
                # Replace both flags; never assemble a PASS from separate sources.
                spawned, returned = codex_rollout_evidence(records, marker)
                source = "codex_rollout"
            except ValueError as error:
                spawned, returned = False, False
                source = None
                reasons.append(str(error))
        if timed_out:
            reasons.append("Harness timed out")
        if code != 0:
            reasons.append(f"Harness exited with code {code}")
        if not spawned:
            reasons.append("No qualifying native child spawn observed")
        if not returned:
            reasons.append("No correlated child result matching the exact marker observed")
        result = {"harness": args.harness, "version": version.stdout.strip(), "exit_code": code, "timed_out": timed_out,
                  "actual_spawn_observed": spawned, "child_marker_result_observed": returned,
                  "evidence_source": source, "incomplete_reasons": reasons,
                  "status": "INCOMPLETE" if reasons else "PASS",
                  "scope": "Generic delegation smoke only; fresh-context semantics require trace inspection; not full interactive workflow acceptance."}
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
