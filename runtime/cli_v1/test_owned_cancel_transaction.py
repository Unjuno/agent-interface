import threading
import time
import unittest
from unittest.mock import Mock

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner


class OwnedCancelTransactionTests(unittest.TestCase):
    def test_concurrent_cancel_cannot_replace_first_cleanup_identity(self):
        owner=object.__new__(OwnedGuardedSessionOwner)
        owner._process=Mock();owner._process.is_alive.return_value=True
        owner._control=Mock();owner._control.poll.return_value=True
        owner._control.recv.return_value={'ok':True,'snapshot':{},'result':{
            'status':'cancel_requested','late_server_request_possible':True}}
        owner._control_lock=threading.Lock();owner._cancel_transaction_lock=threading.Lock()
        owner._rpc_lock=threading.Lock();owner._apply_snapshot=Mock()
        owner._retire=Mock(return_value={'retired':True,'exitcode':-15})
        owner._owner_input_obligations_result_fields=Mock(return_value={})
        owner._execution_unknown=False;owner.review_required=False
        entered=threading.Event();resume=threading.Event();observed=[];results={}
        def cleanup(_retirement):
            if threading.current_thread().name=='first':
                entered.set()
                if not resume.wait(2):raise RuntimeError('fixture timeout')
                observed.append(owner._active_cancel_operation_id)
            return {'status':'unknown'}, {'status':'not_attempted'}
        owner._cleanup_after_owner_retirement=cleanup
        def first():
            try:results['first']=owner.cancel_guarded('first',operation_id='first',deadline_monotonic_ns=time.monotonic_ns()+2_000_000_000)
            except BaseException as error:results['error']=repr(error)
        thread=threading.Thread(target=first,name='first');thread.start()
        self.assertTrue(entered.wait(2),'first did not reach cleanup')
        try:
            results['second']=owner.cancel_guarded('second',operation_id='second',deadline_monotonic_ns=time.monotonic_ns()+80_000_000)
        finally:
            resume.set();thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertNotIn('error',results)
        self.assertEqual(observed,['first'])
        self.assertEqual(results['second']['status'],'cancel_unconfirmed')
        self.assertEqual(results['second']['reason'],'cancel_transaction_deadline')
        self.assertFalse(results['second']['replay_allowed'])
        self.assertEqual(owner._control.send.call_count,1)

if __name__=='__main__':unittest.main()
