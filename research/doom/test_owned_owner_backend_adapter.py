"""Actual selected backend adapter qualification with Fake parent/child X only."""
from contextlib import contextmanager
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from PIL import Image

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'live_control'),str(HERE.parents[1])]
from test_map01_process_identity_backend import FakeDisplay,native,policy,SignalReader,Executor
from doom_process_identity_backend_v1 import Backend
from test_input_owner_process_v3 import fake_owner,edges
from test_input_owner_cancel_v4 import fake_owner_inflight
from input_owner_process_v3 import launch_owner_service

ROWS=[]


def configure_geometry(fake):
    fake.root.id=1
    fake.root.get_full_property=lambda *_:NS(value=[41])
    fake.root.translate_coords=lambda *_:NS(x=0,y=0)
    window=NS(id=41,get_geometry=lambda:NS(width=32,height=32),
              get_attributes=lambda:NS(map_state=native.X.IsViewable))
    fake.create_resource_object=lambda *_:window
    fake.intern_atom=lambda _:1
    return fake


@contextmanager
def child_geometry(*,display,out,service_id):
    with fake_owner(display=display,out=out,service_id=service_id) as owner:
        # Fake Display is already returned by the fixture; geometry is read by
        # the actual native owner surface_context operation.
        configure_geometry(native.display.Display.return_value)
        yield owner


@contextmanager
def child_geometry_inflight(*,display,out,service_id):
    with fake_owner_inflight(display=display,out=out,service_id=service_id) as owner:
        configure_geometry(native.display.Display.return_value)
        yield owner


@contextmanager
def parent_backend(temp,service):
    fake=configure_geometry(FakeDisplay());generation=['a'*64];events=[]
    class Reader:
        def read(self,op,xid):return 41 if op=='focus_id' else generation[0]
        def close(self):pass
    with patch.object(native.display,'Display',side_effect=AssertionError('external backend constructed a local input owner')),patch.object(
            policy,'X11TargetQueries',side_effect=lambda _:Reader()),patch(
            'doom_typed_coast_backend_v1.ImageGrab.grab',return_value=Image.new('RGB',(32,32),'white')):
        session=NS(name=':fake',d=fake,context=lambda:{'windows':'fake'})
        backend=Backend(session,Path(temp),events.append,{n:SignalReader(n) for n in ('health','ammo')},owner_service=service)
        try:yield backend,events,generation
        finally:backend.close()


class OwnedBackendTests(unittest.TestCase):
    def test_adapter_available(self):
        self.assertIsNotNone(importlib.util.find_spec('input_owner_service_adapter'),'production owner/custody adapter absent')

    def inert_adapter(self):
        from input_owner_service_adapter import OwnedOwnerAdapter
        adapter=OwnedOwnerAdapter.__new__(OwnedOwnerAdapter)
        adapter._lock=threading.RLock();adapter._obligation=None;adapter._records=[]
        adapter._attempted=set();adapter._leases={};adapter._close_result=None;adapter._closed=False;adapter._closing=False
        adapter.owner_id='inert-owner';adapter.service_id='inert-service';adapter.timeout=.1;adapter.close_timeout=.1
        adapter.client=NS(close=lambda:{'verified':True},call=lambda *_:{'verified':False},records=[])
        adapter.control=NS(close=lambda:None,outcomes={})
        adapter.service=NS(close_channel=lambda:None,wait=lambda _:dict(verified=True,process_alive=False,exit_code=0))
        return adapter

    def test_unverified_release_retains_adapter_obligation(self):
        adapter=self.inert_adapter();result=adapter.call('release')
        self.assertFalse(result['verified']);self.assertIsNotNone(adapter.obligation_snapshot())
        ROWS.append(dict(case='unverified-release',retained=True,scope='inert owner result; no process'))

    def test_concurrent_close_cannot_upgrade_an_observed_unknown(self):
        adapter=self.inert_adapter();entered=threading.Event();resume=threading.Event();completed=[]
        def close():
            entered.set()
            if not resume.wait(2):raise RuntimeError('test close resume deadline')
            return {'verified':True}
        adapter.client.close=close
        thread=threading.Thread(target=lambda:completed.append(adapter.close()))
        thread.start()
        try:
            self.assertTrue(entered.wait(1));first=adapter.close();self.assertFalse(first['verified'])
            resume.set();thread.join(2);self.assertFalse(thread.is_alive())
            self.assertFalse(completed[0]['verified'],'an already observed unresolved close cannot upgrade')
            self.assertIsNotNone(adapter.obligation_snapshot())
            ROWS.append(dict(case='concurrent-close',first=first,after=completed[0],retained=True,scope='owned local thread/inert clients; no child'))
        finally:resume.set();thread.join(2)

    def test_partial_adapter_startup_attempts_all_cleanup_and_retains_handle(self):
        import input_owner_service_adapter as adapter_api
        outcomes=[]
        for secondary in (False,True):
            actions=[];primary=OSError('injected cancellation readiness')
            service=NS(startup=dict(display=':fake',cancellation_enabled=True,owner_id='inert-owner',service_id='inert-service'),
                take_socket=lambda:object(),take_cancellation_socket=lambda:object(),close_channel=lambda:actions.append('channels'))
            def close():
                actions.append('ordinary')
                if secondary:raise KeyboardInterrupt('injected ordinary close')
            with patch.object(adapter_api.rpc,'OwnerRpcClient',return_value=NS(close=close)),patch.object(
                    adapter_api,'CancellationClient',side_effect=primary):
                with self.assertRaises(BaseExceptionGroup if secondary else OSError) as caught:
                    adapter_api.OwnedOwnerAdapter(service,display=':fake')
            self.assertIs(caught.exception.owner_service_handle,service)
            self.assertEqual(actions,['ordinary','channels'])
            if not secondary:self.assertIs(caught.exception,primary)
            outcomes.append(dict(secondary=secondary,cleanup=actions,owned_handle_retained=True))
        ROWS.append(dict(case='startup-cleanup',outcomes=outcomes,scope='inert clients; no process'))

    def test_external_window_lifecycle_rejected_before_resources(self):
        with self.assertRaises(ValueError):Backend(None,None,None,None,window_lifecycle=True,owner_service=object())
        ROWS.append(dict(case='window-lifecycle-refused',before_resources=True,scope='inert options; no process'))

    def test_surface_context_rejects_bad_request_and_quarantines_bad_geometry(self):
        import input_owner_rpc_v2 as rpc
        request=dict(schema=rpc.SCHEMA,service_id='inert-service',request_id=1,op='surface_context',lease=None,key=41)
        self.assertEqual(rpc._request(request,1,'inert-service'),'surface_context')
        for key in (True,0,1,2**32,'41'):
            with self.subTest(key=key),self.assertRaises(ValueError):rpc._request(dict(request,key=key),1,'inert-service')
        client=rpc.OwnerRpcClient.__new__(rpc.OwnerRpcClient)
        client._sock=object();client._buffer=bytearray();client._gate=threading.Lock();client._records=[]
        client._closed=False;client._quarantined=False;client._next_id=1;client.timeout=.1
        client.display=':fake';client.service_id='inert-service'
        response=dict(schema=rpc.RESPONSE,service_id='inert-service',request_id=1,ok=True,
                      result=[0,0,0,32],records=[],error=None)
        with patch.object(rpc,'_send_frame') as send,patch.object(rpc,'_read_frame',return_value=response):
            with self.assertRaises(rpc.RpcOutcomeUnknown):client.call('surface_context',key=41)
            with self.assertRaises(rpc.RpcQuarantined):client.call('surface_context',key=41)
            self.assertEqual(send.call_count,1)
        ROWS.append(dict(case='surface-validation',invalid_xids_refused=5,bad_geometry_quarantined=True,
                         sends=1,scope='inert framing; no socket/process'))

    def run_case(self,case):
        with tempfile.TemporaryDirectory() as temp:
            service=launch_owner_service(display=':fake',out=Path(temp)/'service',
                _owner_factory=child_geometry_inflight if case=='inflight' else child_geometry,cancellation=True)
            row=dict(case=case);executor=None;resume=threading.Event();entered=threading.Event()
            try:
                with parent_backend(temp,service) as (backend,events,generation):
                    if case=='stale':generation[0]='b'*64
                    backend.snapshot('source',0)
                    row['observation']=[e for e in events if e.get('event')=='observation'][-1]
                    with self.assertRaises(ValueError):backend.validate([{'op':'hold','keys':['a'],'duration_ms':5},
                        {'op':'pointer_click','x':0,'y':0}])
                    self.assertEqual(edges(service.out),[]);row['pointer_program_refused']=True
                    original=backend.raw
                    def raw(key,down):
                        result=original(key,down)
                        if down and case in ('cancel','blocked'):
                            entered.set()
                            if not resume.wait(6):raise RuntimeError('test worker resume deadline')
                        return result
                    backend.raw=raw
                    executor=Executor(backend,events.append)
                    executor.submit(case,[{'op':'hold','keys':['a'],'duration_ms':5}],backend.sequence,
                                    time.perf_counter_ns()+10_000_000_000)
                    worker=executor.active[2] if executor.active else None
                    if case in ('cancel','blocked','inflight'):
                        if case=='inflight':
                            deadline=time.monotonic()+2
                            while not (service.out/'fixture-down-return-blocked').exists() and time.monotonic()<deadline:time.sleep(.005)
                            self.assertTrue((service.out/'fixture-down-return-blocked').exists())
                        else:self.assertTrue(entered.wait(2))
                        if case=='blocked':(service.out/'fixture-block-release').touch()
                        self.assertTrue(executor.cancel(case))
                        if case=='blocked':
                            outcome=backend.owner.control.wait(backend.lease.intent_token,3)
                            self.assertFalse(outcome['release_verified'])
                            row['first_control']=outcome
                            self.assertIsNotNone(backend.owner.obligation_snapshot())
                            (service.out/'fixture-resume-release').touch()
                        else:
                            self.assertIsNotNone(backend.lease.wait_interruption(2))
                            self.assertTrue(backend.owner.control.wait(backend.lease.intent_token,2)['release_verified'])
                        row['before_resume']=dict(worker_alive=worker.is_alive(),resume_set=resume.is_set(),edges=edges(service.out),
                            cause=backend.lease.interruption_snapshot(),custody=backend.executor_custody_snapshot())
                        self.assertTrue(worker.is_alive());resume.set();(service.out/'fixture-resume-down').touch()
                    if worker:worker.join(4)
                    self.assertFalse(worker and worker.is_alive())
                    terminal=[e for e in events if e.get('event')=='terminal'][-1]
                    row.update(terminal=terminal,events=events,owner_records=backend.owner.records,
                               owner_obligation=backend.owner.obligation_snapshot(),custody=backend.executor_custody_snapshot())
                    if case=='blocked':
                        self.assertEqual(terminal['status'],'failed');self.assertFalse(terminal['release']['verified'])
                        self.assertIsNotNone(executor.release_obligation_snapshot())
                        with self.assertRaises(ValueError):executor.submit('replacement',[],backend.sequence,time.perf_counter_ns()+1_000_000_000)
                        executor.close()
                        with self.assertRaises(ValueError):Executor(backend,events.append)
                        row['replacement_refused']=True
                    elif case=='stale':
                        self.assertNotEqual(terminal['status'],'completed');self.assertEqual(edges(service.out),[])
                    else:
                        self.assertEqual(terminal['status'],'completed' if case=='normal' else 'cancelled')
                        self.assertTrue(terminal['release']['verified'])
                    executor.close();row['adapter_close']=backend.close()
                    if case=='blocked':
                        self.assertFalse(row['adapter_close']['verified'])
                        self.assertEqual(backend.close(),row['adapter_close'])
                        row['close_unchanged']=True
            finally:
                resume.set();(service.out/'fixture-resume-release').touch();(service.out/'fixture-resume-down').touch()
                if executor:executor.close()
                service.close_channel();row.update(startup=service.startup,spawn_pid=service.process.pid,
                    service_report=service.wait(6),files=service.saved_files(),edges=edges(service.out))
                row['parent_artifacts']={}
                for path in sorted(Path(temp).rglob('*')):
                    if path.is_file() and not path.is_relative_to(service.out):
                        raw=path.read_bytes();row['parent_artifacts'][path.relative_to(temp).as_posix()]=dict(
                            sha256=hashlib.sha256(raw).hexdigest(),bytes_b64=base64.b64encode(raw).decode('ascii'))
                ROWS.append(row)
                self.assertFalse(service.process.is_alive(),'owned service still alive')

    def test_actual_binding_and_executor_normal(self):self.run_case('normal')
    def test_actual_executor_cancel_before_worker_resume(self):self.run_case('cancel')
    def test_actual_executor_inflight_ordinary_reply(self):self.run_case('inflight')
    def test_first_control_failure_retained_after_late_release(self):self.run_case('blocked')
    def test_stale_parent_source_is_refused(self):self.run_case('stale')


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OwnedBackendTests))
    Path(sys.argv[1]).write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        skipped=len(result.skipped),optimize=sys.flags.optimize,rows=ROWS),indent=2)+'\n',encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())
