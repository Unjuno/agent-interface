import unittest
from pathlib import Path
from runner import command
from mount_adapter import guard_output
from audit_commands import commands

class OutputLayout(unittest.TestCase):
    def test_nested_frozen_output_is_rejected_not_weakened(self):
        here=Path(__file__).resolve().parent
        with self.assertRaises(ValueError):guard_output(here.parent/'predecessor',here/'readiness-raw',here)
        guard_output(here.parent/'predecessor',here.parent/'a03-external-raw',here)
    def test_explicit_new_freeze_reaches_both_native_commands(self):
        argv=command('/source','/output','readiness','readiness-v2-FREEZE.json')
        self.assertIn('/src/readiness-v2-FREEZE.json',argv)
        f={'mode':'readiness','freeze_file':'readiness-v2-FREEZE.json','guest_source':'/source',
           'guest_wrapper':'/raw','guest_audit':'/audit','host_raw':'/host/raw','host_audit':'/host/audit'}
        self.assertIn('/src/readiness-v2-FREEZE.json',commands(f)['audit_native_argv'])

if __name__=='__main__':unittest.main()
