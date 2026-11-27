"""Deadline send state-machine tests; no native input or windows."""
import multiprocessing
import sys
import threading
import time
import unittest
from runtime.guarded_win32_v1.win32_pipe_send import send_before
from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor

def _delayed_fake_recovery(connection, ready, release_effect):
    ready.set()
    time.sleep(2.5)
    try:
        connection.recv()
    except (EOFError, OSError):
        return
    release_effect.set()

def _normal_fake_recovery(connection, ready, release_effect):
    ready.set()
    request=connection.recv()
    release_effect.set()
    connection.send({"release_accepted":True,"request_id":request["request_id"]})
    connection.send({"control":"operation_complete","request_id":request["request_id"]})
    time.sleep(1.0)

class RecoveryOwner:
    def __init__(self):self.unknown=[];self.completed=[]
    def mark_unknown(self, operation_id, generation, reason):
        self.unknown.append((operation_id, generation, reason))
    def recovery_completed(self, *args, **kwargs):self.completed.append((args, kwargs))

class Overlapped:
    event=42
    def __init__(self, length):self.length=length;self.cancelled=False;self.waited=False
    def cancel(self):self.cancelled=True
    def GetOverlappedResult(self, wait):
        if wait:raise AssertionError("must never block for result")
        return self.length,0
class API:
    ERROR_IO_PENDING=997; WAIT_OBJECT_0=0;WAIT_TIMEOUT=258
    def __init__(self, wait_result):self.wait_result=wait_result;self.ov=None
    def WriteFile(self, handle, data, overlapped):
        self.ov=Overlapped(len(data));return self.ov,self.ERROR_IO_PENDING
    def WaitForMultipleObjects(self, events, all_events, timeout):
        self.timeout=timeout;return self.wait_result
class Pipe:
    _send_ov=None
    def _check_closed(self):pass
    def _check_writable(self):pass
    def fileno(self):return 1

class PipeSendTests(unittest.TestCase):
    def test_completed_send_clears_overlapped_state(self):
        p=Pipe();api=API(0);send_before(p,{"x":1},1_000_000_000,clock_ns=lambda:0,api=api)
        self.assertIsNone(p._send_ov)
    def test_timeout_cancels_and_retains_pending_operation(self):
        p=Pipe();api=API(258)
        with self.assertRaises(TimeoutError):send_before(p,{"x":1},1_000_000_000,clock_ns=lambda:0,api=api)
        self.assertTrue(api.ov.cancelled)
        self.assertIs(p._send_ov,api.ov)
        self.assertIs(p._deadline_pending[0],api.ov)
    def test_late_completion_is_not_accepted(self):
        p=Pipe();api=API(0);times=iter((0,0,1_000_000_000))
        with self.assertRaises(TimeoutError):
            send_before(p,{"x":1},1_000_000_000,clock_ns=lambda:next(times),api=api)
        self.assertIsNone(p._send_ov)

    def test_pending_operation_cannot_be_reused(self):
        p=Pipe();api=API(258)
        with self.assertRaises(TimeoutError):send_before(p,{"x":1},1_000_000_000,clock_ns=lambda:0,api=api)
        with self.assertRaises(RuntimeError):send_before(p,{"x":2},1_000_000_000,clock_ns=lambda:0,api=api)

    def test_unconfirmed_result_retains_and_cancels_operation(self):
        p=Pipe();api=API(0)
        original=api.WriteFile
        def failed_result(*args,**kwargs):
            ov,err=original(*args,**kwargs)
            def fail(_wait):raise OSError("unconfirmed")
            ov.GetOverlappedResult=fail
            return ov,err
        api.WriteFile=failed_result
        with self.assertRaises(OSError):send_before(p,{"x":1},1_000_000_000,clock_ns=lambda:0,api=api)
        self.assertTrue(api.ov.cancelled)
        self.assertIs(p._send_ov,api.ov)

    def test_partial_completed_write_is_not_accepted(self):
        p=Pipe();api=API(0);original=api.WriteFile
        def partial(*args,**kwargs):
            ov,err=original(*args,**kwargs)
            ov.GetOverlappedResult=lambda wait:(ov.length-1,0)
            return ov,err
        api.WriteFile=partial
        with self.assertRaises(OSError):send_before(p,{"x":1},1_000_000_000,clock_ns=lambda:0,api=api)
        self.assertIsNone(p._send_ov)

    def test_cancel_failure_does_not_discard_pending_write(self):
        p=Pipe();api=API(258);original=api.WriteFile
        def uncancellable(*args,**kwargs):
            ov,err=original(*args,**kwargs)
            def fail():raise OSError("cancel unavailable")
            ov.cancel=fail
            return ov,err
        api.WriteFile=uncancellable
        with self.assertRaises(TimeoutError):send_before(p,{"x":1},1_000_000_000,clock_ns=lambda:0,api=api)
        self.assertIs(p._send_ov,api.ov)
        self.assertIs(p._deadline_pending[0],api.ov)

    def test_expired_deadline_does_not_start_write(self):
        p=Pipe();api=API(0)
        with self.assertRaises(TimeoutError):send_before(p,{"x":1},10,clock_ns=lambda:10,api=api)
        self.assertIsNone(api.ov)

class ShutdownSendTests(unittest.TestCase):
    def test_shutdown_uses_deadline_send_and_retires_after_timeout(self):
        class Process:
            def __init__(self):self.alive=True
            def is_alive(self):return self.alive
            def close(self):pass
        class Connection:
            def __init__(self):self.closed=False
            def close(self):self.closed=True
        process=Process();connection=Connection();calls=[]
        sup=object.__new__(OperationCancellationSupervisor)
        sup._clock_ns=lambda:100;sup._startup_timeout_s=1
        sup._terminate_grace_s=.01;sup._kill_grace_s=.01
        sup._helpers={"recovery":{"process":process,"connection":connection,"lock":threading.Lock(),"available":True}}
        def timeout(conn, value, deadline):
            calls.append((conn,value,deadline));raise TimeoutError("inert timeout")
        sup._send_helper_request=timeout
        sup._retire_process=lambda proc,deadline:setattr(proc,"alive",False)
        sup._close_helpers()
        self.assertEqual(calls,[(connection,None,100_000_100)])
        self.assertFalse(process.alive)
        self.assertTrue(connection.closed)

@unittest.skipUnless(sys.platform == "win32", "uses Windows overlapped pipes")
class RealPipeRecoveryTests(unittest.TestCase):
    def test_small_request_reaches_fake_helper_and_returns_receipt(self):
        ctx=multiprocessing.get_context("spawn")
        parent,child=ctx.Pipe(duplex=True);ready=ctx.Event();effect=ctx.Event()
        peer=ctx.Process(target=_normal_fake_recovery,args=(child,ready,effect),daemon=True)
        peer.start();child.close()
        sup=object.__new__(OperationCancellationSupervisor)
        sup._clock_ns=time.monotonic_ns;sup._poll_interval_s=.01
        sup._terminate_grace_s=.01;sup._kill_grace_s=.01
        sup._process_identity_reader=lambda _:"fake-identity"
        sup._helpers={"recovery":{"process":peer,"connection":parent,"lock":threading.Lock(),"available":True,"identity":"fake-identity"}}
        try:
            self.assertTrue(ready.wait(2))
            receipt=sup._exchange_helper("recovery",{"request_id":"normal"},time.monotonic_ns()+2_000_000_000)
            self.assertTrue(receipt["release_accepted"])
            self.assertTrue(effect.is_set())
            self.assertTrue(sup._helpers["recovery"]["available"])
            self.assertIsNone(parent._send_ov)
        finally:
            if peer.is_alive():peer.terminate();peer.join(2)
            parent.close()

    def test_timeout_never_confirms_delayed_fake_release(self):
        ctx=multiprocessing.get_context("spawn")
        parent,child=ctx.Pipe(duplex=True);ready=ctx.Event();effect=ctx.Event()
        peer=ctx.Process(target=_delayed_fake_recovery,args=(child,ready,effect),daemon=True)
        peer.start();child.close()
        sup=object.__new__(OperationCancellationSupervisor)
        sup._clock_ns=time.monotonic_ns;sup._poll_interval_s=.01
        sup._terminate_grace_s=.01;sup._kill_grace_s=.01
        sup._process_identity_reader=lambda _:"fake-identity"
        sup._owner=RecoveryOwner()
        sup._helpers={"recovery":{"process":peer,"connection":parent,"lock":threading.Lock(),"available":True,"identity":"fake-identity"}}
        obligations=[f"unicode:{i:04X}" for i in range(63488)]
        thread=None; errors=[]
        try:
            self.assertTrue(ready.wait(2))
            deadline=time.monotonic_ns()+600_000_000
            request={"operation_id":"a"*32,"target_generation":"b"*64,"recovery_id":"c"*32,"deadline_ns":deadline,"obligations":obligations}
            def run_recovery():
                try:sup._run_recovery(request["operation_id"],request["target_generation"],request)
                except BaseException as error:errors.append(error)
            thread=threading.Thread(target=run_recovery,daemon=True)
            thread.start();thread.join(1.5)
            self.assertEqual(errors,[])
            self.assertFalse(thread.is_alive(),"exchange did not return in the test window")
            self.assertFalse(sup._helpers["recovery"]["available"])
            self.assertEqual(len(sup._owner.unknown),1)
            self.assertEqual(sup._owner.unknown[0][2],"recovery_process_exceeded_execution_window")
            self.assertEqual(sup._owner.completed,[])
            peer.join(1)
            self.assertFalse(peer.is_alive(),"owned helper was not retired")
            self.assertFalse(effect.is_set(),"delayed fake release ran")
            with self.assertRaises(RuntimeError):
                sup._exchange_helper("recovery",{"request_id":"late"},time.monotonic_ns()+300_000_000)
            self.assertFalse(effect.is_set())
        finally:
            if peer.is_alive():peer.terminate();peer.join(2)
            if thread is not None:thread.join(2)
            parent.close()

if __name__=="__main__":unittest.main()
