import tempfile,unittest
from unittest.mock import Mock
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from runtime.cli_v1.test_mcp_process_identity import FakeX

class CloseRetry(unittest.TestCase):
    def test_retry_after_worker_failure_records_close_once(self):
        fake=FakeX(self)
        with tempfile.TemporaryDirectory() as td:
            owner=GuardedSessionOwner({'app':20},td);owner.get()
            bridge=owner.bridge;bridge.session.recovery_required=True
            journal=Mock();bridge._receipt_journal=journal
            stop=Mock(side_effect=[RuntimeError('fixture'),None,None]);bridge.stop_target_queries=stop
            with self.assertRaises(RuntimeError):owner.close()
            row=bridge.recover_input(bridge.binding_revision)
            self.assertEqual(row.get('error'),'RECOVERY_REQUIRES_OPEN_SESSION')
            report=owner.close();self.assertEqual(report['receipt_journal']['status'],'close_receipt_recorded')
            self.assertEqual(journal.append.call_count,1)
            owner.close();self.assertEqual(journal.append.call_count,1)
if __name__=='__main__':unittest.main(verbosity=2)
