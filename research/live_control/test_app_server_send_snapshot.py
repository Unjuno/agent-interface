"""Sent-journal snapshot must match serialized wire despite later caller edits."""
import json
import os
import unittest
from unittest.mock import patch

from research.live_control import codex_app_server_client_v2 as module
from test_app_server_known_eof import client_fixture


class SendSnapshotTests(unittest.TestCase):
    def check(self, timing):
        message = {'method': 'unicode', 'params': {'text': '原文\\"\n', 'nested': [1, {'ok': True}]}}
        expected = json.loads(json.dumps(message))
        recorded = []

        def edit():
            message['params']['text'] = 'changed'
            message['params']['nested'][1]['ok'] = False

        def record(direction, snapshot):
            if timing == 'before':
                edit()
            recorded.append((direction, json.loads(json.dumps(snapshot))))
            if timing == 'after':
                edit()

        with client_fixture() as (client, read_fd), patch.object(client, '_record', record):
            client._write(message)
            raw = os.read(read_fd, 4096)
            self.assertEqual(raw, (json.dumps(expected, separators=(',', ':'))+'\n').encode())
            self.assertEqual(recorded, [('sent', expected)])
            self.assertEqual(json.loads(raw), recorded[0][1])
            self.assertFalse(client._send_uncertain)

    def test_healthy_nested_unicode_record_matches_wire(self):
        self.check('healthy')

    def test_caller_edit_before_record_does_not_change_snapshot(self):
        self.check('before')

    def test_caller_edit_after_record_does_not_change_snapshot(self):
        self.check('after')
