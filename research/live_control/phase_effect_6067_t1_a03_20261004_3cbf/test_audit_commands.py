import copy
import unittest
from audit_commands import commands,admit_audit_commands

F={'mode':'readiness','guest_source':'/home/taka/inputs/a03-source','guest_wrapper':'/home/taka/inputs/a03-wrapper',
   'guest_audit':'/home/taka/outputs/a03-audit','host_raw':'/a03/readiness-raw','host_audit':'/a03/readiness-audit'}

class AuditCommands(unittest.TestCase):
    def test_canonical_saved_only_argv(self):
        f={**F,**commands(F)};admit_audit_commands(f)
        self.assertEqual(f['audit_native_argv'],['python3','-B','/src/saved_audit.py','--raw','/raw',
               '--out','/out/result','--freeze','/src/readiness-FREEZE.json'])
        self.assertNotIn('/src/producer.py',f['auditor_command'])
    def test_acquisition_or_changed_transport_is_rejected_before_launch(self):
        f={**F,**commands(F)}
        for key in ('auditor_command','audit_native_argv','audit_stage_command','audit_mkdir_command',
                    'audit_inspect_command','audit_copy_command'):
            changed=copy.deepcopy(f);changed[key][-1]='/src/producer.py'
            with self.subTest(key=key),self.assertRaises(ValueError):admit_audit_commands(changed)

if __name__=='__main__':unittest.main()
