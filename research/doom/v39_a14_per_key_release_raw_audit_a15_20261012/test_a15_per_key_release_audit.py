import ast
import hashlib
import json
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / 'inputs'

def read_json(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))

def read_jsonl(name):
    return [json.loads(line) for line in (DATA / name).read_text(encoding='utf-8').splitlines() if line]

def strict_release_predicate():
    tree = ast.parse((DATA / 'strict_controller.py').read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'terminal_release_is_known_empty')
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'strict_controller.py', 'exec'), namespace)
    return namespace[node.name]

class A14PerKeyRawAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = read_jsonl('events.jsonl')
        cls.report = read_json('report.json')
        cls.protocol = read_jsonl('planner-protocol.jsonl')
        cls.runtime_sources = read_json('runtime-sources.json')
        cls.freeze = read_json('original-freeze.json')
        cls.adapter = read_json('diagnostic-adapter.json')
        cls.rows = [r for r in cls.events if r.get('event') == 'input_release_transition']
        cls.by_id_step = defaultdict(list)
        for row in cls.rows:
            cls.by_id_step[(row.get('id'), row.get('step'))].append(row)

    def test_selected_raw_files_match_original_370_file_manifest(self):
        expected = {}
        for line in (DATA/'raw-sha256sums.txt').read_text(encoding='utf-8').splitlines():
            digest, path = line.split(maxsplit=1)
            expected[path.lstrip('*')] = digest
        mapping = {
            'raw/runtime/events.jsonl': 'events.jsonl',
            'raw/report.json': 'report.json',
            'raw/planner-protocol.jsonl': 'planner-protocol.jsonl',
            'raw/runtime/sources.json': 'runtime-sources.json',
        }
        for archived, local in mapping.items():
            with self.subTest(path=archived):
                self.assertEqual(hashlib.sha256((DATA/local).read_bytes()).hexdigest(), expected[archived])

    def test_protocol_deviation_is_preserved_and_classified(self):
        starts = [r for r in self.protocol if r.get('direction') == 'received' and r.get('message',{}).get('method') == 'turn/started']
        self.assertIn('no planner turn or model call', self.freeze['purpose'])
        self.assertEqual(len(starts), 6)
        self.assertEqual(self.report['planner_turns'], 6)
        self.assertIsNone(self.adapter['diagnostic_sha256'])
        self.assertNotEqual(self.adapter['executed_sha256'], self.freeze['diagnostic_adapter']['diagnostic_sha256'])
        self.assertEqual(self.runtime_sources['doom/session_map01_v12.py'], self.adapter['executed_sha256'])

    def test_all_ten_key_ups_have_identity_bound_xserver_receipts(self):
        self.assertEqual(len(self.rows), 10)
        for row in self.rows:
            with self.subTest(id=row['id'], step=row['step'], key=row['key']):
                receipt = row['owner_thread_keyup_receipt']
                self.assertEqual(row['operation'], 'up')
                self.assertTrue(row['backend_owned_before_release'])
                self.assertFalse(row['owner_cleanup_intervened'])
                self.assertTrue(row['owner_release_history_complete'])
                self.assertTrue(row['owner_thread_keyup_history_complete'])
                self.assertTrue(row['owner_thread_keyup_verified_after_batch'])
                self.assertTrue(row['owner_identity_matches_after_batch'])
                self.assertEqual(row['intent_token'], receipt['intent_token'])
                self.assertEqual(row['owner_id'], receipt['owner_id'])
                self.assertEqual(row['key'], receipt['key'])
                self.assertEqual(row['owner_thread_keyup_receipt_count'], 1)
                self.assertTrue(row['owner_thread_keyup_verified'])
                self.assertEqual(receipt['server_keyup_attempt_count'], 1)
                self.assertTrue(receipt['server_keyup_verified'])
                self.assertTrue(receipt['server_sync_completed'])
                self.assertIsNone(row['owner_explicit_keyup_failure'])
                self.assertIs(receipt['physical_verification_authoritative'], False)
                attempt = receipt['server_keyup_attempts'][0]
                self.assertIsNone(attempt['keyrelease_error'])
                self.assertIsNone(attempt['sync_error'])
                self.assertTrue(attempt['server_key_down_before'])
                self.assertFalse(attempt['server_key_down_after'])
                self.assertLessEqual(attempt['keyrelease_started_ns'], attempt['sync_returned_ns'])
                self.assertLessEqual(attempt['sync_returned_ns'], attempt['keymap_sampled_ns'])
                self.assertLessEqual(attempt['keymap_sampled_ns'], row['release_call_returned_ns'])
                self.assertLessEqual(row['release_call_returned_ns'], row['emit_ns'])
                self.assertEqual(receipt['key_state_source'], 'x11_query_keymap')
                admissions = [e for e in self.events if e.get('event')=='input_admission' and e.get('id')==row['id'] and e.get('step')==row['step'] and e.get('key')==row['key']]
                held = [e for e in self.events if e.get('event')=='keys_held' and e.get('id')==row['id'] and e.get('step')==row['step'] and row['key'] in e.get('keys',[])]
                self.assertEqual(len(admissions), 1)
                self.assertEqual(len(held), 1)
                self.assertLessEqual(admissions[0]['input_ack_ns'], held[0]['input_ack_ns'])
                self.assertLess(held[0]['input_ack_ns'], attempt['keyrelease_started_ns'])

    def test_release_batches_match_ordered_per_key_telemetry(self):
        for (program, step), group in self.by_id_step.items():
            ordered = sorted(group, key=lambda x: x['release_batch_position'])
            self.assertEqual([x['release_batch_position'] for x in ordered], list(range(len(ordered))))
            self.assertEqual({x['release_batch_size'] for x in ordered}, {len(ordered)})
            self.assertEqual({x['release_batch_identifier'] for x in ordered}, {program})
            self.assertEqual({x['step'] for x in ordered}, {step})
            for row in ordered:
                self.assertEqual(row['owner_thread_keyup_receipt']['release_batch_key_order'][row['release_batch_position']], row['key'])
                self.assertEqual(row['release_batch_schema'], 'input-release-batch-v3')
                self.assertEqual(row['transition_schema'], 'input-release-transition-v3')

    def test_two_expiry_cancellations_link_each_step_up_to_strict_terminal(self):
        expected = {'cover-2': 2, 'cover-5': 3}
        for program, count in expected.items():
            group = sorted([r for r in self.rows if r.get('id')==program], key=lambda x:x['emit_ns'])
            released = next(r for r in self.events if r.get('event')=='input_released' and r.get('id')==program)
            terminal = next(r for r in self.events if r.get('event')=='terminal' and r.get('id')==program)
            self.assertEqual(len(group), count)
            self.assertLess(max(r['emit_ns'] for r in group), released['published_ns'])
            self.assertLess(released['published_ns'], terminal['emit_ns'])
            for receipt in [released['owner_release'], terminal['release']]:
                self.assertTrue(receipt['verified'])
                self.assertEqual(receipt['keys_down'], [])
                self.assertEqual(receipt['buttons_down'], [])
                self.assertEqual(receipt['keys_unknown'], [])
                self.assertEqual(receipt['key_state_errors'], [])
                self.assertEqual(receipt['key_state_source'], 'x11_query_keymap')
        predicate = strict_release_predicate()
        for program in expected:
            terminal = next(r for r in self.events if r.get('event')=='terminal' and r.get('id')==program)
            self.assertTrue(predicate(terminal))
            for field in ('keys_unknown','key_state_errors'):
                mutated = json.loads(json.dumps(terminal))
                del mutated['release'][field]
                self.assertFalse(predicate(mutated))

if __name__ == '__main__':
    unittest.main(verbosity=2)
