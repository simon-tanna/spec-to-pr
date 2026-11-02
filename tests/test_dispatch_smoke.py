"""Evidence parsing must never upgrade controller claims into child results."""

import importlib.util
import io
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SOURCE = (
    Path(__file__).resolve().parents[1] / "scripts/evals/run_portable_dispatch_smoke.py"
)
SPEC = importlib.util.spec_from_file_location("dispatch_smoke", SOURCE)
SMOKE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SMOKE)


def rollout():
    """Synthetic native V2 envelopes, matching the observed 0.166.0 record."""
    payloads = [
        {
            "type": "function_call",
            "namespace": "collaboration",
            "name": "spawn_agent",
            "call_id": "spawn",
            "arguments": json.dumps(
                {"task_name": "reader", "fork_turns": "none", "message": "read fixture"}
            ),
        },
        {
            "type": "function_call_output",
            "call_id": "spawn",
            "output": '{"task_name":"/root/reader"}',
        },
        {
            "type": "agent_message",
            "author": "/root/reader",
            "recipient": "/root",
            "content": [
                {
                    "type": "input_text",
                    "text": "Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/reader\nPayload:\nMARK",
                }
            ],
        },
    ]
    return [{"type": "response_item", "payload": p} for p in payloads]


class CodexRolloutEvidence(unittest.TestCase):
    def test_native_fresh_spawn_and_correlated_reply(self):
        self.assertEqual(SMOKE.codex_rollout_evidence(rollout(), "MARK"), (True, True))

    def test_invalid_or_uncorrelated_evidence_cannot_pass(self):
        cases = {}
        for label, index, key, value in [
            ("wrong call", 1, "call_id", "other"),
            ("failed output", 1, "output", '{"error":"spawn failed"}'),
            ("wrong author", 2, "author", "/root/other"),
            ("wrong recipient", 2, "recipient", "/other"),
            ("wrong namespace", 0, "namespace", "tools"),
            ("malformed arguments", 0, "arguments", "{"),
            ("malformed output", 1, "output", "{"),
            ("invalid task", 1, "output", '{"task_name":"reader"}'),
            ("wrong shape", 1, "output", "[]"),
        ]:
            events = rollout()
            events[index]["payload"][key] = value
            cases[label] = events
        for mode in ["all", None]:
            events = rollout()
            args = json.loads(events[0]["payload"]["arguments"])
            args["fork_turns"] = mode
            events[0]["payload"]["arguments"] = json.dumps(args)
            cases[f"context {mode}"] = events
        for text in [
            "MARKsuffix",
            "prefixMARK",
            "different",
            "Message Type: MESSAGE\nPayload:\nMARK",
        ]:
            events = rollout()
            events[2]["payload"]["content"][0]["text"] = text
            cases[text] = events
        events = rollout()
        cases["two spawns"] = [events[0], copy.deepcopy(events[0]), *events[1:]]
        cases["reply before spawn"] = [events[2], *events[:2]]
        cases["no spawn"] = events[1:]
        cases["no output"] = [events[0], events[2]]
        cases["quoted events"] = [
            {"type": "response_item", "payload": {"type": "message", "content": events}}
        ]
        cases["controller only"] = [
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "MARK"},
            }
        ]
        for label, events in cases.items():
            with self.subTest(label=label):
                self.assertNotEqual(
                    SMOKE.codex_rollout_evidence(events, "MARK"), (True, True)
                )

    def test_only_final_answer_payload_matches(self):
        events = rollout()
        events[2]["payload"]["content"][0]["text"] += "\n "
        self.assertEqual(SMOKE.codex_rollout_evidence(events, "MARK"), (True, True))


class CodexRolloutCollection(unittest.TestCase):
    def test_mismatched_metadata_is_checked_before_reading_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self.write_record(root / 'home', root / 'scratch', id='other')
            header = path.read_bytes().split(b'\n', 1)[0] + b'\n'
            path.write_bytes(header + b'\xff unrelated body must not be decoded')
            class GuardedRecord(io.BytesIO):
                def read(self, *args):
                    raise AssertionError('unrelated body must not be read')
            with mock.patch.object(Path, 'open', return_value=GuardedRecord(path.read_bytes())):
                with self.assertRaisesRegex(ValueError, 'metadata does not match'):
                    self.collect(root / 'home', root / 'scratch', root / 'snapshot.jsonl')

    def test_unreadable_record_fails_without_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_record(root / 'home', root / 'scratch')
            out = root / 'snapshot.jsonl'
            with mock.patch.object(Path, 'open', side_effect=PermissionError('unreadable')):
                with self.assertRaisesRegex(ValueError, 'Cannot collect Codex session evidence'):
                    self.collect(root / 'home', root / 'scratch', out)
            self.assertFalse(out.exists())

    def collect(self, home, scratch, out, thread="thread-123"):
        return SMOKE.collect_codex_rollout(thread, scratch, out, home)

    def write_record(
        self, home, scratch, name="rollout-time-thread-123.jsonl", **metadata
    ):
        path = home / "sessions" / "2026" / "11" / "02" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = {"id": "thread-123", "cwd": str(scratch), "source": "exec", **metadata}
        events = [{"type": "session_meta", "payload": meta}, *rollout()]
        path.write_text("".join(json.dumps(e) + "\n" for e in events))
        return path

    def test_custom_home_and_verified_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = self.write_record(root / "home", root / "scratch")
            events = self.collect(
                root / "home", root / "scratch", root / "snapshot.jsonl"
            )
            self.assertEqual(SMOKE.codex_rollout_evidence(events, "MARK"), (True, True))
            self.assertEqual(
                original.read_bytes(), (root / "snapshot.jsonl").read_bytes()
            )

    def test_missing_ambiguous_mismatched_and_malformed_records_fail_closed(self):
        for case in [
            "missing",
            "ambiguous",
            "id",
            "cwd",
            "source",
            "malformed",
            "compressed",
            "invalid thread",
        ]:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                home, scratch, out = (
                    root / "home",
                    root / "scratch",
                    root / "snapshot.jsonl",
                )
                out.write_text("stale")
                if case != "missing":
                    path = self.write_record(home, scratch)
                    if case == "ambiguous":
                        self.write_record(
                            home, scratch, name="rollout-other-thread-123.jsonl"
                        )
                    elif case in ["id", "cwd", "source"]:
                        self.write_record(home, scratch, **{case: "wrong"})
                    elif case == "malformed":
                        path.write_text(path.read_text() + "{broken\n")
                    elif case == "compressed":
                        path.rename(path.with_suffix(".jsonl.zst"))
                with self.assertRaises(ValueError):
                    self.collect(
                        home,
                        scratch,
                        out,
                        "../thread-123" if case == "invalid thread" else "thread-123",
                    )
                self.assertFalse(
                    out.exists(), "a failed collection must not leave stale evidence"
                )


FAKE_CLI = r'''
import json, os, sys, time
from pathlib import Path
if '--version' in sys.argv:
    print('fake-cli 0.166.0')
    sys.exit(0)
mode = os.environ['SMOKE_TEST_MODE']
if mode == 'timeout':
    time.sleep(30)
root = Path.cwd()
marker = (root / 'fixture.txt').read_text().strip()
if Path(sys.argv[0]).name == 'claude':
    print(json.dumps({'type':'tool_use','name':'Agent','id':'child'}))
    print(json.dumps({'type':'tool_result','tool_use_id':'child','content':marker}))
    sys.exit(0)
print(json.dumps({'type':'thread.started','thread_id':'thread-123'}))
if mode in ('legacy', 'mixed'):
    print(json.dumps({'type':'item.completed','item':{'type':'collab_tool_call','tool':'spawn_agent','receiver_thread_ids':['child']}}))
    if mode == 'legacy':
        print(json.dumps({'type':'item.completed','item':{'type':'collab_tool_call','tool':'wait','agents_states':{'child':{'status':'completed','message':marker}}}}))
records = [
    {'type':'session_meta','payload':{'id':'thread-123','source':'exec','cwd':str(root)}},
    {'type':'response_item','payload':{'type':'function_call','name':'spawn_agent','namespace':'collaboration','call_id':'spawn','arguments':json.dumps({'task_name':'reader','fork_turns':'none'})}},
    {'type':'response_item','payload':{'type':'function_call_output','call_id':'spawn','output':'{"task_name":"/root/reader"}'}},
    {'type':'response_item','payload':{'type':'agent_message','author':'/root/reader','recipient':'/root','content':[{'type':'input_text','text':'Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/reader\nPayload:\n'+marker}]}},
]
if mode == 'mixed':
    records = records[:1] + records[3:]
if mode not in ('missing', 'legacy'):
    path = Path(os.environ['CODEX_HOME']) / 'sessions/2026/11/02/rollout-time-thread-123.jsonl'
    path.parent.mkdir(parents=True)
    path.write_text(''.join(json.dumps(r)+'\n' for r in records))
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':marker}}))
if mode == 'timeout-complete':
    import signal
    signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
    sys.stdout.flush()
    time.sleep(30)
sys.exit(2 if mode == 'nonzero' else 0)
'''


class DispatchRunner(unittest.TestCase):
    def run_smoke(self, mode, harness='codex'):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cli = root / harness
            cli.write_text(f'#!{sys.executable}\n' + FAKE_CLI)
            cli.chmod(0o755)
            out = root / 'out'
            out.mkdir()
            (out / 'codex-rollout.jsonl').write_text('stale evidence')
            home = root / 'codex-home'
            home.mkdir()
            config = home / 'config.toml'
            config.write_text('sentinel user configuration')
            env = {**os.environ, 'PATH': str(root) + os.pathsep + os.environ['PATH'],
                   'CODEX_HOME': str(home), 'SMOKE_TEST_MODE': mode}
            completed = subprocess.run([sys.executable, str(SOURCE), '--harness', harness,
                                        '--output', str(out), '--timeout', '1'],
                                       env=env, capture_output=True, text=True, timeout=15)
            result = json.loads((out / 'result.json').read_text())
            command = json.loads((out / 'command.json').read_text())
            self.assertEqual(config.read_text(), 'sentinel user configuration')
            self.assertNotIn((out / 'expected_marker.txt').read_text().strip(), command[-1])
            return completed.returncode, result, command, (out / 'codex-rollout.jsonl').exists()

    def test_codex_v2_passes_with_retained_record_and_isolated_invocation(self):
        code, result, command, snapshot = self.run_smoke('success')
        self.assertEqual((code, result['status'], result['evidence_source']), (0, 'PASS', 'codex_rollout'))
        self.assertTrue(snapshot)
        self.assertNotIn('--ephemeral', command)
        self.assertIn('plugins', command)
        self.assertIn('skip_host_skill_discovery', command)
        self.assertEqual(result['incomplete_reasons'], [])

    def test_legacy_and_claude_use_complete_jsonl_evidence(self):
        for mode, harness in [('legacy', 'codex'), ('success', 'claude')]:
            with self.subTest(harness=harness):
                code, result, _, snapshot = self.run_smoke(mode, harness)
                self.assertEqual((code, result['status'], result['evidence_source']), (0, 'PASS', 'jsonl'))
                self.assertFalse(snapshot)

    def test_missing_mixed_nonzero_and_timeout_cannot_pass(self):
        for mode in ['missing', 'mixed', 'nonzero', 'timeout', 'timeout-complete']:
            with self.subTest(mode=mode):
                code, result, _, snapshot = self.run_smoke(mode)
                self.assertEqual((code, result['status']), (1, 'INCOMPLETE'))
                self.assertTrue(result['incomplete_reasons'])
                if mode in ['missing', 'timeout']:
                    self.assertFalse(snapshot)


class DispatchEvidence(unittest.TestCase):
    def test_observed_codex_wait_without_spawn_is_incomplete(self):
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "collab_tool_call",
                    "tool": "wait",
                    "receiver_thread_ids": [],
                    "agents_states": {},
                    "status": "completed",
                },
            },
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "MARK"},
            },
        ]
        self.assertEqual(SMOKE.evidence(events, "codex", "MARK"), (False, False))

    def test_codex_result_requires_matching_completed_child(self):
        spawn = {
            "type": "collab_tool_call",
            "tool": "spawn_agent",
            "receiver_thread_ids": ["child"],
        }
        for field in ["agents", "agents_states"]:
            for child, status, marker, expected in [
                ("child", "completed", "MARK", True),
                ("other", "completed", "MARK", False),
                ("child", "failed", "MARK", False),
                ("child", "completed", "different", False),
            ]:
                with self.subTest(
                    field=field, child=child, status=status, marker=marker
                ):
                    wait = {
                        "type": "collab_tool_call",
                        "tool": "wait",
                        field: {child: {"status": status, "message": marker}},
                    }
                    self.assertEqual(
                        SMOKE.evidence([spawn, wait], "codex", "MARK"), (True, expected)
                    )

    def test_claude_requires_nonerror_correlated_tool_result(self):
        call = {"type": "tool_use", "name": "Task", "id": "id"}
        for call_id, error, expected in [
            ("id", False, True),
            ("other", False, False),
            ("id", True, False),
        ]:
            with self.subTest(call_id=call_id, error=error):
                result = {
                    "type": "tool_result",
                    "tool_use_id": call_id,
                    "content": "MARK",
                    "is_error": error,
                }
                self.assertEqual(
                    SMOKE.evidence([call, result], "claude", "MARK"), (True, expected)
                )


if __name__ == "__main__":
    unittest.main()
