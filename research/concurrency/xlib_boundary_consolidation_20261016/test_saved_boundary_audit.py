"""Saved-data checks only: never import or execute an archived producer."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('saved_xlib_boundary_audit', HERE / 'audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
PACKET = HERE.parent / 'python_xlib_boundary_17_20261004_70ab'


class SavedBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.document = audit.decode_packet(PACKET)
        self.files = audit.verify_members(self.document)

    def test_original_members_and_named_boundaries(self):
        self.assertEqual(audit.verify_original_paths(HERE.parents[2]), 261)
        self.assertEqual(len(self.files), 274)
        self.assertEqual(audit.verify_boundaries(self.files),
                         ['server_global_stop', 'socket_timeout_not_logical_deadline'])

    def test_member_tampering_is_rejected(self):
        document = copy.deepcopy(self.document)
        name = next(iter(document['files']))
        document['files'][name] = 'dGFtcGVyZWQ='
        with self.assertRaises(ValueError): audit.verify_members(document)

    def test_duplicate_or_missing_projection_members_are_rejected(self):
        for duplicate in (True, False):
            with self.subTest(duplicate=duplicate):
                document = copy.deepcopy(self.document)
                if duplicate: document['projection_manifest'].append(document['projection_manifest'][0])
                else: document['projection_manifest'].pop()
                with self.assertRaises(ValueError): audit.verify_members(document)

    def test_saved_boundary_contradictions_are_rejected(self):
        server = 'xlib-server-stop-70ab/RESULT.json'
        timeout = 'python-xlib-timeout-70ab/RESULT.json'
        mutations = [
            (server, lambda d: d.update(input_emissions=1)),
            (server, lambda d: d['snapshots']['server_stopped'].update(alive=[True, False])),
            (server, lambda d: d['completed']['independent'].update(map='01' * 32)),
            (server, lambda d: d.update(source='wrong-source')),
            (server, lambda d: d['events'][-1].update(ns=d['events'][-2]['ns'] - 1)),
            (server, lambda d: d['events'][0].update(ns=True)),
            (server, lambda d: d['snapshots']['server_stopped'].update(alive=[1, 1])),
            (timeout, lambda d: d['pre_gate'].update(additional_no_reply_hold_ns=True)),
            (timeout, lambda d: d['pre_gate'].update(blocked_alive=[False, True])),
            (timeout, lambda d: d['pre_gate'].update(completed={'independent': [True, 1, 0]})),
            (timeout, lambda d: d.update(actual_input_opcodes=1)),
            (timeout, lambda d: next(e for e in d['events'] if e['kind'] == 'peer_request').update(opcode=255)),
            (timeout, lambda d: next(e for e in d['events'] if e['kind'] == 'query_end' and e['label'] == 'independent').update(ns=d['events'][-1]['ns'] + 1)),
            (timeout, lambda d: next(e for e in d['events'] if e['kind'] == 'query_end' and e['label'] == 'blocked_first').update(ns=d['events'][0]['ns'] - 1)),
        ]
        for index, (name, mutate) in enumerate(mutations):
            with self.subTest(index=index):
                files = dict(self.files)
                value = json.loads(files[name])
                mutate(value)
                files[name] = json.dumps(value).encode()
                with self.assertRaises(ValueError): audit.verify_boundaries(files)


if __name__ == '__main__':
    unittest.main()
