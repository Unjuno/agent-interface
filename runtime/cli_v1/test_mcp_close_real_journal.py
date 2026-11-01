import tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from runtime.cli_v1.test_mcp_process_identity import FakeX
from runtime.guarded_x11_v1.receipt_journal import ReceiptJournal

class CloseRetryRealJournal(unittest.TestCase):
    def test_retry_persists_exactly_one_close_receipt(self):
        fake=FakeX(self)
        with tempfile.TemporaryDirectory() as td:
            owner=GuardedSessionOwner({'app':20},td);owner.get()
            bridge=owner.bridge;bridge.session.recovery_required=True
            journal_path=Path(td)/'retry-journal.jsonl';bridge._receipt_journal=ReceiptJournal(journal_path)
            bridge.stop_target_queries=Mock(side_effect=[RuntimeError('fixture'),None,None])
            with self.assertRaises(RuntimeError):owner.close()
            self.assertEqual(bridge.recover_input(bridge.binding_revision).get('error'),'RECOVERY_REQUIRES_OPEN_SESSION')
            report=owner.close();self.assertEqual(report['receipt_journal']['status'],'close_receipt_recorded')
            stored=ReceiptJournal.read(journal_path,'session-close')
            self.assertEqual(stored['status'],'closed')
            owner.close()
            self.assertEqual(len(journal_path.read_bytes().splitlines()),1)
            self.assertEqual(ReceiptJournal.read(journal_path,'session-close'),stored)
if __name__=='__main__':unittest.main(verbosity=2)
