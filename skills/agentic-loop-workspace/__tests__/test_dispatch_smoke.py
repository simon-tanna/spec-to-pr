"""Evidence parsing must never upgrade controller claims into child results."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'run_portable_dispatch_smoke.py'
SPEC = importlib.util.spec_from_file_location('dispatch_smoke', SOURCE)
SMOKE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SMOKE)


class DispatchEvidence(unittest.TestCase):
    def test_observed_codex_wait_without_spawn_is_incomplete(self):
        events = [
            {'type': 'item.completed', 'item': {'type': 'collab_tool_call', 'tool': 'wait', 'receiver_thread_ids': [], 'agents_states': {}, 'status': 'completed'}},
            {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'MARK'}},
        ]
        self.assertEqual(SMOKE.evidence(events, 'codex', 'MARK'), (False, False))

    def test_codex_result_requires_matching_completed_child(self):
        spawn = {'type': 'collab_tool_call', 'tool': 'spawn_agent', 'receiver_thread_ids': ['child']}
        for field in ['agents', 'agents_states']:
            for child, status, marker, expected in [
                ('child', 'completed', 'MARK', True),
                ('other', 'completed', 'MARK', False),
                ('child', 'failed', 'MARK', False),
                ('child', 'completed', 'different', False),
            ]:
                with self.subTest(field=field, child=child, status=status, marker=marker):
                    wait = {'type': 'collab_tool_call', 'tool': 'wait', field: {child: {'status': status, 'message': marker}}}
                    self.assertEqual(SMOKE.evidence([spawn, wait], 'codex', 'MARK'), (True, expected))

    def test_claude_requires_nonerror_correlated_tool_result(self):
        call = {'type': 'tool_use', 'name': 'Task', 'id': 'id'}
        for call_id, error, expected in [('id', False, True), ('other', False, False), ('id', True, False)]:
            with self.subTest(call_id=call_id, error=error):
                result = {'type': 'tool_result', 'tool_use_id': call_id, 'content': 'MARK', 'is_error': error}
                self.assertEqual(SMOKE.evidence([call, result], 'claude', 'MARK'), (True, expected))


if __name__ == '__main__':
    unittest.main()
