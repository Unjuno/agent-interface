"""Independent cancellation qualification; all input/query/capture is Fake X."""
from contextlib import contextmanager
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'doom'),str(HERE.parents[1])]
from test_input_owner_process_v3 import fake_owner,make_lease,edges
from test_map01_process_identity_backend import backend_fixture,Executor
from input_owner_process_v3 import launch_owner_service
from input_owner_rpc_v2 import OwnerRpcClient,encode_lease

ROWS=[]


def api():
    import input_owner_cancel_v4
    return input_owner_cancel_v4


@contextmanager
def fake_owner_inflight(*,display,out,service_id):
    with fake_owner(display=display,out=out,service_id=service_id) as owner:
        original=owner.call
        def call(op,lease=None,key=None):
            result=original(op,lease,key)
            if op=='down':
                (out/'fixture-down-return-blocked').touch()
                while not (out/'fixture-resume-down').exists():time.sleep(.005)
            return result
        owner.call=call
        yield owner


class CancelRelayTests(unittest.TestCase):
    def test_relay_module_available(self):
        self.assertIsNotNone(importlib.util.find_spec('input_owner_cancel_v4'),
                             'independently serviced cancellation/cause relay absent')

    def launch(self,temp,factory=fake_owner):
        service=launch_owner_service(display=':fake',out=Path(temp)/'service',_owner_factory=factory,cancellation=True)
        client=OwnerRpcClient(service.take_socket(),display=':fake',service_id=service.service_id)
        control=api().CancellationClient(service.take_cancellation_socket(),startup=service.startup,timeout=2)
        return service,client,control

    def finish(self,service,client,control,row):
        (service.out/'fixture-resume-down').touch();(service.out/'fixture-resume-release').touch()
        try:
            row['client_close']=client.close()
        finally:
            control.close();service.close_channel()
            row.update(service_report=service.wait(6),startup=service.startup,spawn_pid=service.process.pid,
                       files=service.saved_files(),edges=edges(service.out),control_outcomes=control.outcomes)
            ROWS.append(row)
        self.assertFalse(service.process.is_alive(),'owned service unresolved')
        self.assertFalse(control.thread_alive,'control watcher unresolved')

    def test_pending_cancel_is_sticky_and_changed_source_rejected(self):
        registry=api().LeaseRegistry();lease=make_lease();dto=encode_lease(lease);dto['cancel_requested']=True
        first=registry.decode(dto);dto['cancel_requested']=False
        self.assertIs(registry.decode(dto),first);self.assertTrue(first.cancel.is_set())
        changed=copy.deepcopy(dto);changed['target_process_identity'][2]='b'*64
        with self.assertRaises(ValueError):registry.decode(changed)
        registry.retire('test control loss')
        with self.assertRaises(RuntimeError):registry.decode(dto)
        ROWS.append(dict(case='registry-binding',pending_cancel_sticky=True,changed_source_refused=True,retired_refused=True))

    def test_secondary_channel_cleanup_cannot_skip_primary_channel(self):
        import input_owner_process_v3 as owned
        class Channel:
            closed=False
            def shutdown(self,_):pass
            def close(self):self.closed=True
        class Bad(Channel):
            def shutdown(self,_):raise KeyboardInterrupt('cancel cleanup interruption')
        main=Channel();cancel=Bad()
        handle=owned.OwnedOwnerService(None,main,'.','inert-generation',os.getpid())
        handle._cancel_channel=cancel
        with self.assertRaises(KeyboardInterrupt):handle.close_channel()
        self.assertTrue(main.closed,'primary transport still must close')
        self.assertTrue(cancel.closed,'secondary close must follow shutdown fault')
        ROWS.append(dict(case='paired-channel-cleanup',both_closed=True,primary_preserved=True,scope='inert channels; no process'))

    def test_cause_validation_rejects_unbound_or_false_release(self):
        dto=encode_lease(make_lease());record=dict(event='owner_release',reason='cancelled',intent_token=dto['intent_token'],
            valid_until_ns=dto['deadline_ns'],target_process_identity=dto['target_process_identity'],
            verified=True,keys_down=[],buttons_down=[],keys_unknown=[],key_state_errors=[],key_state_source='x11_query_keymap')
        cause=dict(intent_token=dto['intent_token'],record=record)
        self.assertTrue(api().validate_cause(cause,dto))
        unverified=copy.deepcopy(cause);unverified['record']['verified']=False
        self.assertFalse(api().validate_cause(unverified,dto))
        for field,value in (('intent_token','wrong'),('valid_until_ns',1),('target_process_identity',[1,41,'b'*64,dto['deadline_ns']]),('reason','close'),('keys_unknown',[38])):
            bad=copy.deepcopy(cause);bad['record'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):api().validate_cause(bad,dto)
        ROWS.append(dict(case='cause-binding',mutants_rejected=5))

    def exercise_executor(self,inflight):
        with tempfile.TemporaryDirectory() as temp,backend_fixture() as (backend,events,_,fake):
            service,client,control=self.launch(temp,fake_owner_inflight if inflight else fake_owner)
            client.owner_id=service.startup['owner_id'];backend.owner.close();backend.owner=client
            resume=threading.Event();entered=threading.Event();executor=None
            row=dict(case='inflight-rpc' if inflight else 'paused-executor')
            original=backend.raw
            def raw(key,down):
                if down:control.watch(backend.lease)
                result=original(key,down)
                if down and not inflight:
                    entered.set()
                    if not resume.wait(5):raise RuntimeError('test worker pause deadline')
                return result
            backend.raw=raw
            try:
                backend.snapshot('source',0);executor=Executor(backend,events.append)
                executor.submit(row['case'],[{'op':'hold','keys':['a'],'duration_ms':5}],backend.sequence,
                                time.perf_counter_ns()+10_000_000_000)
                worker=executor.active[2]
                if inflight:
                    deadline=time.monotonic()+2
                    while not (service.out/'fixture-down-return-blocked').exists() and time.monotonic()<deadline:time.sleep(.005)
                    self.assertTrue((service.out/'fixture-down-return-blocked').exists())
                else:self.assertTrue(entered.wait(2))
                cancelled_at=time.perf_counter_ns();self.assertTrue(executor.cancel(row['case']))
                cause=backend.lease.wait_interruption(2)
                self.assertIsNotNone(cause,'independent cancellation must publish original parent lease cause')
                outcome=control.wait(backend.lease.intent_token,2)
                self.assertTrue(outcome['release_verified']);self.assertTrue(outcome['accepted'])
                deadline=time.monotonic()+1
                while not any(e.get('event')=='input_released' for e in events) and time.monotonic()<deadline:time.sleep(.005)
                self.assertTrue(any(e.get('event')=='input_released' for e in events))
                self.assertTrue(worker.is_alive());self.assertFalse(resume.is_set())
                self.assertEqual([e['event'] for e in edges(service.out)],[2,3])
                row.update(before_resume=dict(cancelled_at_ns=cancelled_at,observed_at_ns=time.perf_counter_ns(),
                    cause=cause,outcome=outcome,worker_alive=worker.is_alive(),resume_set=resume.is_set(),
                    events=copy.deepcopy(events),edges=edges(service.out)),lease=encode_lease(backend.lease))
                resume.set();(service.out/'fixture-resume-down').touch();worker.join(4)
                self.assertFalse(worker.is_alive())
                terminal=[e for e in events if e.get('event')=='terminal'][-1]
                self.assertEqual(terminal['status'],'cancelled');self.assertTrue(terminal['release']['verified'])
                row.update(terminal=terminal,events=events)
            finally:
                resume.set();(service.out/'fixture-resume-down').touch()
                if executor:executor.close()
                self.finish(service,client,control,row)

    def test_actual_executor_receives_release_before_worker_resume(self):self.exercise_executor(False)
    def test_control_is_serviced_while_ordinary_rpc_inflight(self):self.exercise_executor(True)

    def test_blocked_release_first_control_result_never_upgrades(self):
        with tempfile.TemporaryDirectory() as temp:
            service,client,control=self.launch(temp);row=dict(case='blocked-release')
            lease=make_lease()
            try:
                control.watch(lease);client.call('down',lease,'a')
                (service.out/'fixture-block-release').touch();lease.set()
                first=control.wait(lease.intent_token,3)
                self.assertTrue(first['accepted']);self.assertFalse(first['release_verified'])
                self.assertIsNone(lease.interruption_snapshot())
                self.assertEqual([e['event'] for e in edges(service.out)],[2])
                row['before']=dict(outcome=first,edges=edges(service.out),service_alive=service.process.is_alive())
                (service.out/'fixture-resume-release').touch()
                deadline=time.monotonic()+2
                while len(edges(service.out))<2 and time.monotonic()<deadline:time.sleep(.005)
                self.assertEqual([e['event'] for e in edges(service.out)],[2,3])
                self.assertEqual(control.wait(lease.intent_token,.1),first)
                self.assertIsNone(lease.interruption_snapshot())
                row.update(first_unchanged=True,parent_cause=None,lease=encode_lease(lease))
            finally:self.finish(service,client,control,row)

    def test_control_loss_cancels_known_lease_and_retires_admission(self):
        with tempfile.TemporaryDirectory() as temp:
            service,client,control=self.launch(temp);row=dict(case='control-loss')
            lease=make_lease()
            try:
                client.call('down',lease,'a');control.close()
                deadline=time.monotonic()+2
                while len(edges(service.out))<2 and time.monotonic()<deadline:time.sleep(.005)
                self.assertEqual([e['event'] for e in edges(service.out)],[2,3])
                with self.assertRaises(Exception):client.call('down',make_lease(),'a')
                self.assertEqual([e['event'] for e in edges(service.out)],[2,3])
                row['new_down_refused']=True
            finally:self.finish(service,client,control,row)

    def test_wrong_generation_retires_service_control_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            service,client,control=self.launch(temp);row=dict(case='wrong-generation')
            lease=make_lease()
            try:
                client.call('down',lease,'a');dto=encode_lease(lease);dto['cancel_requested']=True
                api().rpc._send_frame(control.sock,dict(schema=api().SCHEMA,service_id='wrong-generation',
                    request_id=1,lease=dto),time.monotonic()+1)
                deadline=time.monotonic()+2
                while len(edges(service.out))<2 and time.monotonic()<deadline:time.sleep(.005)
                self.assertEqual([e['event'] for e in edges(service.out)],[2,3])
                with self.assertRaises(Exception):client.call('down',make_lease(),'a')
                row['new_down_refused']=True
            finally:self.finish(service,client,control,row)

    def test_cancel_before_down_cannot_be_undone_by_later_request(self):
        with tempfile.TemporaryDirectory() as temp:
            service,client,control=self.launch(temp);row=dict(case='cancel-before-down')
            lease=make_lease()
            try:
                control.watch(lease);lease.set();outcome=control.wait(lease.intent_token,3)
                self.assertTrue(outcome['accepted']);self.assertFalse(outcome['release_verified'])
                # A stale ordinary sender cannot clear the registered cancellation.
                lease.cancel.clear()
                with self.assertRaises(Exception):client.call('down',lease,'a')
                self.assertEqual(edges(service.out),[])
                row.update(outcome=outcome,new_down_refused=True)
            finally:self.finish(service,client,control,row)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CancelRelayTests))
    Path(sys.argv[1]).write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        skipped=len(result.skipped),optimize=sys.flags.optimize,rows=ROWS),indent=2)+'\n',encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())
