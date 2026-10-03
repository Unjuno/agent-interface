import copy
import json
from pathlib import Path
import unittest
from audit_v2 import identity_errors

HERE = Path(__file__).resolve().parent


class Identity(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads((HERE / 'formal/01/run/raw.json').read_text())

    def test_original_native_identities(self):
        self.assertEqual(identity_errors(self.raw), [])

    def test_signal_pid_float(self):
        row = self.raw['rows'][4]; row['signals'][0]['pid'] = float(row['pids']['owner'])
        self.assertIn('A05/signal-pid-type', identity_errors(self.raw))

    def test_signal_pid_boolean(self):
        self.raw['rows'][4]['signals'][0]['pid'] = True
        self.assertIn('A05/signal-pid-type', identity_errors(self.raw))

    def test_display_namespace(self):
        self.raw['rows'][4]['display'] = ':999'
        self.assertIn('A05/display', identity_errors(self.raw))

    def test_display_alias(self):
        self.raw['rows'][4]['display'] = ':103'
        self.assertIn('A05/display', identity_errors(self.raw))

    def test_owner_role(self):
        self.raw['rows'][4]['owner_ready']['role'] = 'consumer'
        self.assertIn('A05/ready-role', identity_errors(self.raw))

    def test_consumer_role(self):
        self.raw['rows'][4]['consumer_ready']['role'] = 'owner'
        self.assertIn('A05/ready-role', identity_errors(self.raw))


if __name__ == '__main__': unittest.main()
