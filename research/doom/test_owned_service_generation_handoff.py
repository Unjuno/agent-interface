"""Fake-X sequential owner handoff; no game or model."""
import tempfile, time, unittest, threading, socket
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
import copy
from contextlib import contextmanager
import test_owned_owner_backend_adapter as fixtures
import session_owned_owner_backend as session_backend
from pathlib import Path
from test_owned_owner_backend_adapter import child_geometry, parent_backend, SignalReader, Executor
from input_owner_process_v3 import launch_owner_service

@contextmanager
def close_order_barrier(*,display,out,service_id):
    import input_owner_cancel_v4 as lane
    original=lane.CancellationService.close
    def delayed_close(self):
        self.thread.join(3)
        return original(self)
    with patch.object(lane.CancellationService,"close",delayed_close):
        with child_geometry(display=display,out=out,service_id=service_id) as owner:
            yield owner

class OwnedServiceHandoffTests(unittest.TestCase):
    def inert_generation(self):
        backend=session_backend.Backend.__new__(session_backend.Backend)
        backend._session_lock=threading.RLock(); backend._executor_custody_lock=threading.RLock()
        backend._rotation_broken=False; backend._session_close=None; backend._owner_generation=0
        backend._consumed_rotation_terminals=set(); backend._executor_custody_owner=None
        backend._executor_release_obligation=None; backend._startup_hash="start"; backend._archived_owner_records=[]
        backend._session_out=Path("/unused"); backend.owner=NS(owner_id="old",obligation_snapshot=lambda:None,
            close=Mock(return_value={"verified":True}),records=[])
        backend.owned_service=NS(service_id="old-service")
        terminal={"event":"terminal","id":"old-action","status":"cancelled","input_owner_generation":0,
            "input_owner_id":"old","release":{"verified":True,"keys_down":[],"buttons_down":[],"keys_unknown":[],
            "key_state_errors":[],"target_process_identity_reader":{"retired":True}}}
        return backend,terminal

    def test_close_receipt_publication_failure_prevents_new_service(self):
        backend,terminal=self.inert_generation()
        with patch.object(session_backend,"publish_json_exclusive",side_effect=OSError("injected")), \
             patch.object(session_backend,"launch_owner_service") as launch:
            with self.assertRaises(OSError): backend.rotate_input_owner_after_cancel(terminal)
            launch.assert_not_called()
        self.assertTrue(backend._rotation_broken)
        with self.assertRaisesRegex(ValueError,"no new authority"): backend.claim_executor_custody(object())

    def test_unqualified_interruption_never_retires_owner(self):
        backend,terminal=self.inert_generation();terminal.update(status="needs_decision",interruption={"intent_token":"t","record":{}})
        with self.assertRaisesRegex(ValueError,"qualified interruption"):
            backend.rotate_input_owner_after_cancel(terminal)
        backend.owner.close.assert_not_called();self.assertFalse(backend._rotation_broken)

    def test_qualified_interruption_can_reach_owned_rotation(self):
        backend,terminal=self.inert_generation();backend.session=NS(name=":fake");backend._owner_factory=None
        record={"event":"owner_release","intent_token":"t","reason":"target_query_invalidated","verified":True,
                "keys_down":[],"buttons_down":[],"keys_unknown":[],"key_state_errors":[],
                "target_process_identity_reader":{"retired":True},
                "key_release_attempts":{"38":{"verified":True,"attempts":[{"attempt":1,
                    "keyrelease_started_ns":10,"sync_returned_ns":11,"keymap_sampled_ns":12,
                    "server_key_down_before":True,"server_key_down_after":False}]}}}
        terminal.update(status="needs_decision",interruption={"intent_token":"t","record":record})
        failure=RuntimeError("injected-new-launch")
        with patch.object(session_backend,"publish_json_exclusive",return_value="archive"), \
             patch.object(session_backend,"launch_owner_service",side_effect=failure):
            with self.assertRaisesRegex(RuntimeError,"injected-new-launch"):
                backend.rotate_input_owner_after_cancel(terminal)
        backend.owner.close.assert_called_once()

    def test_failed_new_launch_keeps_owned_handle_and_revokes_authority(self):
        backend,terminal=self.inert_generation();backend.session=NS(name=":fake");backend._owner_factory=None
        handle=NS(service_id="new-service",close_channel=Mock(),wait=Mock(return_value={"verified":False}))
        failure=RuntimeError("startup failed");failure.owner_service_handle=handle
        with patch.object(session_backend,"publish_json_exclusive",return_value="archive"), \
             patch.object(session_backend,"launch_owner_service",side_effect=failure):
            with self.assertRaises(RuntimeError):backend.rotate_input_owner_after_cancel(terminal)
        self.assertIs(backend._rotation_handle,handle)
        self.assertTrue(backend._rotation_broken)
        with self.assertRaisesRegex(ValueError,"no new authority"):backend.claim_executor_custody(object())

    def test_final_close_cannot_upgrade_failed_rotation(self):
        backend,_=self.inert_generation(); backend._rotation_broken=True; backend._session_error=None
        with tempfile.TemporaryDirectory() as temp:
            backend._session_out=Path(temp)
            with patch.object(session_backend.Previous,"close",return_value={"verified":True}):
                with self.assertRaises(session_backend.OwnerServiceCleanupUnverified): backend.close()
            self.assertFalse(backend._session_close["verified"])

    def test_executor_claim_cannot_race_failed_rotation(self):
        backend,_=self.inert_generation(); backend._provided_input_owner=None
        class RaceLock:
            def __enter__(self): backend._rotation_broken=True
            def __exit__(self,*args): pass
        backend._executor_custody_lock=RaceLock()
        with self.assertRaisesRegex(ValueError,"no new authority"):
            backend.claim_executor_custody(object())
        self.assertIsNone(backend._executor_custody_owner)

    def test_generation_change_before_lock_prevents_retiring_wrong_owner(self):
        backend,terminal=self.inert_generation()
        class RaceLock:
            def __enter__(self): backend._owner_generation=1
            def __exit__(self,*args): pass
        backend._session_lock=RaceLock()
        with patch.object(session_backend,"publish_json_exclusive") as publish, \
             patch.object(session_backend,"launch_owner_service") as launch:
            with self.assertRaisesRegex(ValueError,"generation"):
                backend.rotate_input_owner_after_cancel(terminal)
            backend.owner.close.assert_not_called(); publish.assert_not_called(); launch.assert_not_called()

    def test_unverified_old_close_prevents_new_service(self):
        backend,terminal=self.inert_generation(); backend.owner.close.return_value={"verified":False}
        with patch.object(session_backend,"launch_owner_service") as launch:
            with self.assertRaises(session_backend.OwnerServiceCleanupUnverified): backend.rotate_input_owner_after_cancel(terminal)
            launch.assert_not_called()
        self.assertTrue(backend._rotation_broken)

    def test_control_eof_before_verified_owner_close_remains_error(self):
        from input_owner_cancel_v4 import CancellationClient, CancellationService
        left,right=socket.socketpair(); flag=threading.Event()
        startup={"display":":fake","service_id":"test","owner_id":"owner","cancellation_enabled":True}
        service=CancellationService(left,display=":fake",service_id="test",owner_id="owner",normal_close=flag)
        client=CancellationClient(right,startup=startup)
        try:
            client.close(); service.thread.join(2)
            self.assertFalse(service.thread.is_alive()); self.assertIn("EOFError",service.error)
        finally: service.close()

    def test_partial_control_frame_stays_error_after_owner_close(self):
        from input_owner_cancel_v4 import CancellationClient, CancellationService
        left,right=socket.socketpair(); flag=threading.Event()
        startup={"display":":fake","service_id":"test","owner_id":"owner","cancellation_enabled":True}
        service=CancellationService(left,display=":fake",service_id="test",owner_id="owner",normal_close=flag)
        client=CancellationClient(right,startup=startup)
        try:
            right.sendall(b"{"); flag.set(); client.close(); service.thread.join(2)
            self.assertFalse(service.thread.is_alive()); self.assertIsNotNone(service.error)
        finally:service.close()

    def test_ordered_ordinary_close_then_control_detach_is_clean(self):
        with tempfile.TemporaryDirectory() as temp:
            service=launch_owner_service(display=":fake",out=Path(temp)/"old",_owner_factory=close_order_barrier,cancellation=True)
            with parent_backend(temp,service): pass
            report=service.wait(5)
            self.assertTrue(report["verified"]); self.assertIsNone(report["recovery"]["service_error"])

    def test_session_advertises_only_explicit_owned_rotation_capability(self):
        import session_map01_v12 as session
        predicate=getattr(session,"supports_owner_generation_rotation",lambda backend:False)
        backend=NS(rotate_input_owner_after_cancel=lambda terminal:None,window_identity=None,
                   _provided_input_owner=object(),owned_generation_rotation_supported=True)
        self.assertTrue(predicate(backend))
        backend.owned_generation_rotation_supported=False;self.assertFalse(predicate(backend))
        backend.owned_generation_rotation_supported=True;backend.window_identity=object();self.assertFalse(predicate(backend))
        backend.window_identity=None;backend.rotate_input_owner_after_cancel=None;self.assertFalse(predicate(backend))

    def test_actual_new_child_start_failure_retains_handle_and_blocks_future_authority(self):
        from test_input_owner_process_v3 import fake_owner_start_error
        with tempfile.TemporaryDirectory() as temp:
            def selected(*args,**kwargs):
                kwargs.pop("owner_service",None)
                return session_backend.Backend(*args,**kwargs,_owner_factory=child_geometry)
            with patch.object(fixtures,"Backend",selected):
                with self.assertRaises(session_backend.OwnerServiceCleanupUnverified):
                    with parent_backend(temp,None) as (backend,events,_):
                        backend.snapshot("source",0);executor=Executor(backend,events.append)
                        executor.submit("old",[{"op":"hold","keys":["a"],"duration_ms":1000}],backend.sequence,time.perf_counter_ns()+10_000_000_000)
                        deadline=time.monotonic()+3
                        while not any(x.get("event")=="keys_held" for x in events) and time.monotonic()<deadline:time.sleep(.005)
                        self.assertTrue(any(x.get("event")=="keys_held" for x in events))
                        worker=executor.active[2];self.assertTrue(executor.cancel("old"));worker.join(4)
                        self.assertFalse(worker.is_alive());executor.close()
                        terminal=copy.deepcopy(next(x for x in events if x.get("event")=="terminal" and x.get("id")=="old"))
                        terminal["release"]["target_process_identity_reader"]={"retired":True,"pending":False,"thread_alive":False}
                        terminal["input_owner_generation"]=backend._owner_generation;terminal["input_owner_id"]=backend.owner.owner_id
                        backend._owner_factory=fake_owner_start_error
                        with self.assertRaises(Exception):backend.rotate_input_owner_after_cancel(terminal)
                        self.assertTrue(backend._rotation_broken);self.assertIsNotNone(backend._rotation_handle)
                        self.assertFalse(backend._rotation_handle.process.is_alive())
                        with self.assertRaisesRegex(ValueError,"no new authority"):backend.claim_executor_custody(object())
                self.assertFalse(backend._session_close["verified"])

    def test_backend_rotates_verified_cancelled_owner_and_invalidates_source(self):
        with tempfile.TemporaryDirectory() as temp:
            def selected(*args,**kwargs):
                kwargs.pop("owner_service",None)
                return session_backend.Backend(*args,**kwargs,_owner_factory=child_geometry)
            with patch.object(fixtures,"Backend",selected):
                with parent_backend(temp,None) as (backend,events,_):
                    backend.snapshot("source",0)
                    executor=Executor(backend,events.append)
                    executor.submit("old",[{"op":"hold","keys":["a"],"duration_ms":1000}],backend.sequence,time.perf_counter_ns()+10_000_000_000)
                    deadline=time.monotonic()+3
                    while not any(x.get("event")=="keys_held" for x in events) and time.monotonic()<deadline:time.sleep(.005)
                    self.assertTrue(any(x.get("event")=="keys_held" for x in events))
                    worker=executor.active[2]; self.assertTrue(executor.cancel("old")); worker.join(4)
                    self.assertFalse(worker.is_alive())
                    terminal=copy.deepcopy(next(x for x in events if x.get("event")=="terminal" and x.get("id")=="old"))
                    self.assertEqual(terminal["status"],"cancelled"); self.assertTrue(terminal["release"]["verified"])
                    # Synthetic snapshot exercises the branch; no real X is used.
                    terminal["release"]["target_process_identity_reader"]={"retired":True,"pending":False,"thread_alive":False}
                    terminal["input_owner_generation"]=backend._owner_generation; terminal["input_owner_id"]=backend.owner.owner_id
                    old=backend.owned_service
                    from input_owner_generation_protocol_v1 import InputOwnerGenerationProtocol
                    protocol=InputOwnerGenerationProtocol(); protocol.record_terminal(terminal,backend)
                    replacement,receipt=protocol.rotate({"op":"rotate_input_owner","id":"old"},
                        executor=executor,backend=backend,executor_factory=lambda b:Executor(b,events.append))
                    self.assertTrue(old.wait(5)["verified"]); self.assertFalse(old.process.is_alive())
                    self.assertNotEqual(backend.owner.owner_id,terminal["input_owner_id"])
                    self.assertEqual(receipt["generation"],1); self.assertIsNone(backend._source_identity)
                    self.assertFalse(receipt["grants_input_authority"])
                    from lease import Lease
                    from executor_v3 import DecisionRequired
                    with self.assertRaises(DecisionRequired):
                        backend.bind_lease_source(Lease(time.perf_counter_ns()+1_000_000_000),backend.sequence)
                    refresh=protocol.refresh_source({"op":"refresh_owner_source","id":"old"},backend=backend)
                    self.assertFalse(refresh["grants_input_authority"]);self.assertIsNotNone(backend._source_identity)
                    replacement.submit("new",[{"op":"hold","keys":["a"],"duration_ms":5}],backend.sequence,time.perf_counter_ns()+10_000_000_000)
                    worker=replacement.active[2] if replacement.active else None
                    if worker:worker.join(4);self.assertFalse(worker.is_alive())
                    final=next(x for x in events if x.get("event")=="terminal" and x.get("id")=="new")
                    self.assertEqual(final["status"],"completed");self.assertTrue(final["release"]["verified"])
                    replacement.close()

    def test_verified_cancel_close_then_fresh_owner_accepts_new_action(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"old-capture").mkdir(); (root/"new-capture").mkdir()
            old=launch_owner_service(display=":fake",out=root/"old",_owner_factory=child_geometry,cancellation=True)
            with parent_backend(root/"old-capture",old) as (backend,events,_):
                backend.snapshot("old-source",0)
                executor=Executor(backend,events.append)
                executor.submit("old",[{"op":"hold","keys":["a"],"duration_ms":1000}],backend.sequence,time.perf_counter_ns()+10_000_000_000)
                deadline=time.monotonic()+3
                while not any(x.get("event")=="keys_held" for x in events) and time.monotonic()<deadline:
                    time.sleep(.005)
                self.assertTrue(any(x.get("event")=="keys_held" for x in events))
                worker=executor.active[2]
                self.assertTrue(executor.cancel("old")); worker.join(4); self.assertFalse(worker.is_alive())
                terminal=next(x for x in events if x.get("event")=="terminal" and x.get("id")=="old")
                self.assertEqual(terminal["status"],"cancelled"); self.assertTrue(terminal["release"]["verified"])
                executor.close()
            old_report=old.wait(5)
            self.assertTrue(old_report["verified"]); self.assertFalse(old_report["process_alive"])
            new=launch_owner_service(display=":fake",out=root/"new",_owner_factory=child_geometry,cancellation=True)
            self.assertNotEqual(old.owner_id if hasattr(old,"owner_id") else old.startup["owner_id"],new.startup["owner_id"])
            with parent_backend(root/"new-capture",new) as (backend,events,_):
                backend.snapshot("new-source",0)
                executor=Executor(backend,events.append)
                executor.submit("new",[{"op":"hold","keys":["a"],"duration_ms":5}],backend.sequence,time.perf_counter_ns()+10_000_000_000)
                worker=executor.active[2] if executor.active else None
                if worker:worker.join(4)
                terminal=next(x for x in events if x.get("event")=="terminal" and x.get("id")=="new")
                self.assertEqual(terminal["status"],"completed");self.assertTrue(terminal["release"]["verified"])
                executor.close()
            self.assertTrue(new.wait(5)["verified"])

if __name__=="__main__":unittest.main()
