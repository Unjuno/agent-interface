"""Actual executor/backend/owner integration using isolated Fake X only."""
from contextlib import contextmanager
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
from PIL import Image
from pathlib import Path
from test_owned_owner_backend_adapter import parent_backend,child_geometry,Executor,native,edges,configure_geometry,FakeDisplay,policy,SignalReader
from input_owner_process_v3 import launch_owner_service
from map01_door_task_contract import DoorTaskContract, _hold_duration_verified
from input_owner_generation_protocol_v1 import InputOwnerGenerationProtocol

@contextmanager
def child_immediate_identity(*,display,out,service_id):
    """Keep identity reads immediate; separate tests exercise their stalls."""
    with child_geometry(display=display,out=out,service_id=service_id) as owner:
        reader=owner._inner.identity_reader
        reader.read_focus=lambda xid, *, perf_deadline_ns, cancelled: 41
        reader.read=lambda xid, *, perf_deadline_ns, cancelled: "a"*64
        yield owner

class TimedHoldIntegrationTests(unittest.TestCase):
    def test_cancel_during_blocked_observation_releases_before_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            service=launch_owner_service(display=":fake",out=Path(temp)/"service",_owner_factory=child_geometry,cancellation=True,timed_up=True)
            executor=None;entered=threading.Event();resume=threading.Event()
            try:
                with parent_backend(temp,service) as (backend,events,generation):
                    backend._timed_hold_enabled=True;backend.snapshot("source",0);snapshot=backend.snapshot
                    def blocked(identifier,index):
                        if identifier=="timed-cancel" and backend.held:
                            entered.set()
                            if not resume.wait(4):raise RuntimeError("test observation was not resumed")
                        return snapshot(identifier,index)
                    backend.snapshot=blocked;executor=Executor(backend,events.append)
                    executor.submit("timed-cancel",[{"op":"hold","keys":["a"],"duration_ms":1500}],backend.sequence,time.perf_counter_ns()+10_000_000_000)
                    worker=executor.active[2] if executor.active else None
                    self.assertTrue(entered.wait(3));self.assertTrue(executor.cancel("timed-cancel"))
                    outcome=backend.owner.control.wait(backend.lease.intent_token,3)
                    self.assertTrue(outcome["release_verified"])
                    self.assertTrue(any(row["event"]==native.X.KeyRelease for row in edges(service.out)))
                    self.assertTrue(worker.is_alive())
                    resume.set();worker.join(6);self.assertFalse(worker.is_alive())
                    terminal=[row for row in events if row.get("event")=="terminal"][-1]
                    self.assertEqual(terminal["status"],"cancelled",terminal)
                    self.assertTrue(terminal["release"]["verified"])
                    executor.close();executor=None
            finally:
                resume.set()
                if executor is not None:executor.close()
                service.close_channel();service.process.join(5)
                self.assertFalse(service.process.is_alive())
    def test_observation_failure_releases_and_allows_fresh_operation(self):
        with tempfile.TemporaryDirectory() as temp:
            service=launch_owner_service(display=":fake",out=Path(temp)/"service",_owner_factory=child_immediate_identity,cancellation=True,timed_up=True)
            executor=None
            try:
                with parent_backend(temp,service) as (backend,events,generation):
                    backend._timed_hold_enabled=True;backend.snapshot("source",0);snapshot=backend.snapshot
                    def failing(identifier,index):
                        if identifier=="fail" and backend.held:raise RuntimeError("injected observation failure")
                        return snapshot(identifier,index)
                    backend.snapshot=failing;executor=Executor(backend,events.append)
                    executor.submit("fail",[{"op":"hold","keys":["a"],"duration_ms":400}],backend.sequence,time.perf_counter_ns()+10_000_000_000)
                    first=executor.active[2] if executor.active else None
                    if first:first.join(6)
                    self.assertFalse(first and first.is_alive())
                    terminal=[row for row in events if row.get("event")=="terminal" and row.get("id")=="fail"][-1]
                    self.assertNotEqual(terminal["status"],"completed")
                    self.assertTrue(terminal["release"]["verified"])
                    self.assertIsNone(backend.owner.obligation_snapshot())
                    backend.snapshot("new-source",0)
                    executor.submit("next",[{"op":"hold","keys":["a"],"duration_ms":150}],backend.sequence,time.perf_counter_ns()+10_000_000_000)
                    second=executor.active[2] if executor.active else None
                    if second:second.join(6)
                    self.assertFalse(second and second.is_alive())
                    self.assertEqual([row for row in events if row.get("event")=="terminal" and row.get("id")=="next"][-1]["status"],"completed")
                    executor.close();executor=None
            finally:
                if executor is not None:executor.close()
                service.close_channel();service.process.join(5)
                self.assertFalse(service.process.is_alive())
    def test_ambiguous_release_publication_is_not_retried_or_upgraded(self):
        with tempfile.TemporaryDirectory() as temp:
            service=launch_owner_service(display=":fake",out=Path(temp)/"service",_owner_factory=child_immediate_identity,cancellation=True,timed_up=True)
            executor=None
            try:
                with parent_backend(temp,service) as (backend,events,generation):
                    backend._timed_hold_enabled=True;backend.snapshot("source",0)
                    emit=backend._external_emit
                    def fail_after_delivery(row):
                        emit(row)
                        if row.get("event")=="input_release_transition":raise RuntimeError("injected ambiguous sink")
                    backend._external_emit=fail_after_delivery
                    executor=Executor(backend,events.append)
                    executor.submit("ambiguous",[{"op":"hold","keys":["a"],"duration_ms":200}],backend.sequence,time.perf_counter_ns()+10_000_000_000)
                    worker=executor.active[2] if executor.active else None
                    if worker:worker.join(6)
                    self.assertFalse(worker and worker.is_alive())
                    terminal=[r for r in events if r.get("event")=="terminal" and r.get("id")=="ambiguous"][-1]
                    self.assertEqual(terminal["status"],"failed")
                    # Physical neutrality and publication delivery are distinct evidence.
                    self.assertTrue(terminal["release"]["verified"])
                    delivery=terminal["release"]["release_batch_delivery"]
                    self.assertEqual([r["state"] for r in delivery["positions"]],["unknown"])
                    self.assertEqual(len([r for r in events if r.get("event")=="input_release_transition"]),1)
                    self.assertEqual(len([r for r in edges(service.out) if r["event"]==native.X.KeyRelease]),1)
                    executor.close();executor=None
            finally:
                if executor is not None:executor.close()
                service.close_channel();service.process.join(5)
                self.assertFalse(service.process.is_alive())
    def test_timed_mode_rejects_multi_key_before_input(self):
        with tempfile.TemporaryDirectory() as temp:
            service=launch_owner_service(display=":fake",out=Path(temp)/"service",_owner_factory=child_geometry,cancellation=True,timed_up=True)
            try:
                with parent_backend(temp,service) as (backend,events,generation):
                    backend._timed_hold_enabled=True
                    with self.assertRaises(ValueError):backend.validate([{"op":"hold","keys":["a","d"],"duration_ms":100}])
                    self.assertEqual(edges(service.out),[])
            finally:
                service.close_channel();service.process.join(5)
                self.assertFalse(service.process.is_alive())
    def test_selected_owned_backend_enables_timed_hold_end_to_end(self):
        from session_owned_owner_backend import Backend
        with tempfile.TemporaryDirectory() as temp:
            fake=configure_geometry(FakeDisplay());events=[]
            class Reader:
                def read(self,op,xid):return 41 if op=='focus_id' else 'a'*64
                def close(self):pass
            with patch.object(native.display,'Display',side_effect=AssertionError('unexpected local owner')),patch.object(
                    policy,'X11TargetQueries',side_effect=lambda _:Reader()),patch(
                    'doom_typed_coast_backend_v1.ImageGrab.grab',return_value=Image.new('RGB',(32,32),'white')):
                session=NS(name=':fake',d=fake,context=lambda:{'windows':'fake'})
                backend=Backend(session,Path(temp),events.append,{n:SignalReader(n) for n in ('health','ammo')},
                                _owner_factory=child_immediate_identity,timed_hold=True)
                executor=None
                try:
                    self.assertIs(backend.owned_service.startup.get('timed_up_enabled'),True)
                    backend.snapshot('source',0);executor=Executor(backend,events.append)
                    executor.submit('selected',[{'op':'hold','keys':['a'],'duration_ms':200}],backend.sequence,time.perf_counter_ns()+10_000_000_000)
                    worker=executor.active[2] if executor.active else None
                    if worker:worker.join(6)
                    self.assertFalse(worker and worker.is_alive())
                    terminal=[r for r in events if r.get('event')=='terminal'][-1]
                    self.assertEqual(terminal['status'],'completed',terminal)
                    self.assertEqual([r for r in events if r.get('event')=='input_release_transition'][-1]['release_mode'],'owner_deadline')
                    executor.close();executor=None
                finally:
                    if executor is not None:executor.close()
                    backend.close()
    def test_slow_observation_does_not_hold_key_past_timer(self):
        with tempfile.TemporaryDirectory() as temp:
            service=launch_owner_service(display=":fake",out=Path(temp)/"service",_owner_factory=child_immediate_identity,cancellation=True,timed_up=True)
            executor=None;observed=[]
            try:
                with parent_backend(temp,service) as (backend,events,generation):
                    backend._timed_hold_enabled=True
                    backend.snapshot("source",0)
                    snapshot=backend.snapshot
                    def slow_snapshot(identifier,index):
                        if identifier=="timed" and backend.held:
                            time.sleep(.45)
                            observed.append(any(row["event"]==native.X.KeyRelease for row in edges(service.out)))
                        return snapshot(identifier,index)
                    backend.snapshot=slow_snapshot
                    executor=Executor(backend,events.append)
                    valid_until=time.perf_counter_ns()+10_000_000_000
                    first_deadline=time.perf_counter_ns()+2_000_000_000
                    steps=[{"op":"hold","keys":["a"],"duration_ms":200}]
                    executor.submit("timed",steps,backend.sequence,valid_until,admission_deadline_ns=first_deadline)
                    worker=executor.active[2] if executor.active else None
                    if worker:worker.join(6)
                    self.assertFalse(worker and worker.is_alive())
                    terminal=[row for row in events if row.get("event")=="terminal"][-1]
                    self.assertEqual(terminal["status"],"completed",terminal)
                    self.assertEqual(observed,[True])
                    transitions=[row for row in events if row.get("event")=="input_release_transition"]
                    self.assertEqual(len(transitions),1)
                    self.assertEqual(transitions[0].get("release_mode"),"owner_deadline")
                    self.assertTrue(transitions[0].get("owner_transition_verified"))
                    self.assertIn("scheduled",transitions[0]["measurement_contract_v3"])
                    down=next(row for row in events if row.get("event")=="input_admission")
                    held=next(row for row in events if row.get("event")=="keys_held")
                    transition=transitions[0];up=transition["owner_thread_keyup_receipt"]
                    self.assertTrue(_hold_duration_verified(down,held,transition,up,200))
                    self.assertEqual(transition["admission_receipt"],dict({k:v for k,v in down.items() if k!="emit_ns"},operation="down"))
                    accepted=next(row for row in events if row.get("event")=="accepted" and row.get("id")=="timed")
                    target=down["target_process_identity"]
                    InputOwnerGenerationProtocol().record_terminal(terminal,backend)
                    gate=DoorTaskContract("use");gate.inflight="timed";gate.steps=steps
                    gate.identity=(down["owner_id"],terminal["input_owner_generation"],target[1],target[2],"unused")
                    gate.sequence=target[0];gate.valid_until=valid_until;gate.deadline=first_deadline
                    gate.completed("timed",terminal,accepted,events)
                    executor.close();executor=None
            finally:
                if executor is not None:executor.close()
                service.close_channel();service.process.join(5)
                self.assertFalse(service.process.is_alive())

if __name__=="__main__":unittest.main()
