"""Compiled semantic checks under cancellation, Fake X transport only."""
import copy
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from PIL import Image
from Xlib import X
from runtime.cli_v1.test_mcp_process_identity import FakeX
from runtime.guarded_x11_v1.test_observation_worker import reader_backend
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from runtime.guarded_x11_v1.compiled import _Adapter
from research.live_control.integrated_efficiency_compiled_adapter_v2 import (
    compile_form_method, EXPECTED_METHOD_CONTRACT,
)
from research.live_control.integrated_efficiency_compiled_execution_v2 import run_compiled_interface_in_caller

ROWS=[]


class CompiledObservationCancellationTests(unittest.TestCase):
    def cell(self, isolated, trigger):
        fake=FakeX(self);phase=[0];clock_offset=[0];real_clock=time.monotonic_ns
        initial=Image.frombytes('RGB',(32,32),fake.raw,'raw','BGRX')
        initial.putpixel((31,31),(0,0,0));fake.raw=initial.tobytes('raw','BGRX')
        original_emit=fake.emit;timeline=[]
        def mark(event,**values):timeline.append(dict(event=event,real_monotonic_ns=real_clock(),**values))
        def emit(display,kind,code):
            original_emit(display,kind,code)
            mark('fake_emission',kind=kind,code=code,phase=phase[0],thread=threading.get_ident())
            if kind==X.KeyRelease and code==1:
                phase[0]+=1
                image=Image.frombytes('RGB',(32,32),fake.raw,'raw','BGRX')
                image.putpixel((31,31),(phase[0],0,0));fake.raw=image.tobytes('raw','BGRX')
        fake.backend.d.create_resource_object=lambda kind,xid:SimpleNamespace(id=xid)
        fake.backend.d.get_display_name=lambda:':fake-qualified'
        entered,resume,reader_closed=threading.Event(),threading.Event(),threading.Event()
        reader=reader_backend(fake,lambda *a:SimpleNamespace(data=fake.raw,depth=24,visual=1))
        reader.d.create_resource_object=lambda kind,xid:SimpleNamespace(id=xid)
        reader.d.close=lambda:reader_closed.set()
        results,errors,callback_threads,outer=[],[],[],[];holder={}
        with tempfile.TemporaryDirectory(prefix='compiled-observation-stop-') as td, \
                patch('time.monotonic_ns',side_effect=lambda:real_clock()+clock_offset[0]), \
                patch('runtime.backends.x11_v1.backend.xtest.fake_input',side_effect=emit), \
                patch('runtime.guarded_x11_v1.observation_worker.open_readonly_backend',return_value=reader), \
                patch('runtime.guarded_x11_v1.observation_worker.read_linux_x11_process_identity',side_effect=lambda *a:fake.generation), \
                patch('runtime.guarded_x11_v1.target_queries.X11TargetQueries') as query:
            query.return_value.read.side_effect=lambda op,xid:True if op=='focus' else fake.generation
            bridge=NativeHandleBridge(':fake-qualified',{'app':20},'app',Path(td)/'bridge',
                process_identity=True,query_worker=True,observation_worker=isolated)
            source=bridge.observe()
            offsets={a:bridge.mint(a,source['sequence'],p,region_size=[12,12])
                for a,p in [('field',[8,8]),('submit',[24,8])]}
            def perceive(native,image):
                if trigger!='none' and phase[0]==1 and 1 in fake.down:
                    callback_threads.append(threading.get_ident());mark('callback_entered');entered.set()
                    if not resume.wait(5):raise TimeoutError('owned callback not resumed')
                    mark('callback_resumed')
                n=image.getpixel((31,31))[0]
                return dict(field_target_present=True,submit_target_present=True,
                    field_pixels_changed=n>0,field_value_matches_task=n>0,
                    submission_pixels_changed=n>1)
            def build(payload):
                interface=compile_form_method(interface_id='isolated-caller',session_scope=bridge.scope,
                    surface='x11-window-20',field_handle=payload['target']['field'],
                    submit_handle=payload['target']['submit'],method_contract=EXPECTED_METHOD_CONTRACT)
                holder['adapter']=_Adapter(bridge,interface,
                    {a:dict(interaction='keyboard',offset=offsets[alias],
                        tail=[{'op':'key_chord','keys':['CTRL','a']}])
                        for a,alias in [('enter_token','field'),('submit_form','submit')]},
                    perceive,lambda payload,*a:dict(status='succeeded',evidence_ref=payload['observation']['evidence_ref']),
                    lambda:False)
                holder['interface']=interface
                return interface
            def callback(name):return lambda payload:getattr(holder['adapter'],name)(payload)
            def verify_outer(payload):
                outer.append(copy.deepcopy(payload));return dict(status='unavailable',evidence_ref='synthetic-outer')
            def invoke():
                try:
                    with bridge.cancellation_scope('compiled-call'):
                        results.append(run_compiled_interface_in_caller(
                            dict(target='synthetic',route='reuse',coarse_origin='caller_provided',provided_coarse=None,
                                cached_target={'field':'field','submit':'submit'},repair_on=[],local_repair_on=[],session_id='fake'),
                            dict(reuse_revalidate=lambda _:{'status':'revalidated'},
                                final_revalidate=lambda _:{'status':'revalidated'},verify_effect=verify_outer),build,
                            {**{name:callback(name) for name in ('observe','admit','execute','verify_effect')},
                             'cancelled':lambda:False}))
                        mark('caller_returned')
                except BaseException as error:errors.append(dict(type=type(error).__name__,error=repr(error)))
            worker=threading.Thread(target=invoke);worker.start();before_resume=None
            try:
                if trigger!='none':
                    self.assertTrue(entered.wait(2),(results,errors))
                    self.assertEqual(fake.down,{1})
                    mark('control_requested',trigger=trigger)
                    if trigger=='cancel':
                        control=bridge.request_cancel('compiled-call')
                        self.assertEqual(control['status'],'cancel_requested')
                    else:
                        control={'original_deadline':bridge.deadline}
                        clock_offset[0]=bridge.deadline-real_clock()+1000
                    worker.join(2 if isolated else .1)
                    before_resume=dict(writer_alive=worker.is_alive(),resume_set=resume.is_set(),
                        down=sorted(fake.down),emissions=copy.deepcopy(fake.emissions),
                        results=copy.deepcopy(results),control=control,sequence=bridge.sequence,
                        observation_worker=bridge._observations.snapshot() if isolated else None)
                    self.assertFalse(resume.is_set())
                    if isolated:
                        self.assertFalse(worker.is_alive(),errors);self.assertEqual(fake.down,set())
                        self.assertTrue(before_resume['observation_worker']['retired'])
                        self.assertTrue(before_resume['observation_worker']['thread_alive'])
                        self.assertEqual(len(results),1)
                    else:
                        self.assertTrue(worker.is_alive());self.assertEqual(fake.down,{1});self.assertEqual(results,[])
                    mark('callback_resume_requested');resume.set()
                worker.join(2);self.assertFalse(worker.is_alive(),errors);self.assertEqual(errors,[])
                self.assertEqual(len(results),1)
                if isolated and trigger!='none':
                    self.assertTrue(reader_closed.wait(2))
                    self.assertEqual(results,before_resume['results'])
                    self.assertEqual(bridge.sequence,before_resume['sequence'])
                    self.assertNotIn(worker.ident,callback_threads)
                elif trigger!='none':self.assertEqual(set(callback_threads),{worker.ident})
                result=results[0];core=result['compiled_execution_receipt']
                terminals=[e for e in core['critical_events'] if e['event']=='action_terminal']
                self.assertTrue(all(e['release_verified'] for e in terminals))
                if trigger=='none':
                    self.assertEqual(result['outcome'],'TASK_NOT_VERIFIED')
                    self.assertEqual(core['completed_transitions'],2)
                    self.assertEqual(fake.emissions,[(2,1),(2,2),(3,2),(3,1)]*2)
                    refused=None
                else:
                    self.assertEqual(result['outcome'],'EXECUTION_INCOMPLETE')
                    self.assertEqual(core['completed_transitions'],1)
                    self.assertEqual(outer,[])
                    self.assertEqual(fake.emissions,[(2,1),(2,2),(3,2),(3,1),(2,1),(3,1)])
                    self.assertTrue(bridge.review_required)
                    adapter=holder['adapter'];interface=holder['interface']
                    refused=adapter.admit(dict(interface_id=interface['interface_id'],session_scope=bridge.scope,
                        action='submit_form',operation='activate_submit',symbol=interface['symbols']['submit_control'],
                        observation=adapter.latest))
                    self.assertFalse(refused['eligible']);self.assertEqual(refused['status'],'association_changed')
                self.assertEqual(fake.down,set())
                bridge.close()
                for client in (bridge._target_queries,bridge._observations):
                    if client is not None and client.thread is not None:
                        client.thread.join(2);self.assertFalse(client.thread.is_alive())
                row=dict(isolated=isolated,trigger=trigger,before_resume=before_resume,result=result,
                    emissions=copy.deepcopy(fake.emissions),down=sorted(fake.down),errors=errors,outer_checks=outer,
                    reused_admission=refused,callback_threads=callback_threads,writer_thread=worker.ident,
                    timeline=timeline,
                    observation_worker=bridge._observations.snapshot() if isolated else None,
                    guard_restored=bridge._input_guard is None,pending_authorizations=len(holder['adapter'].authorizations),
                    files_hex={p.relative_to(td).as_posix():p.read_bytes().hex() for p in Path(td).rglob('*') if p.is_file()})
                ROWS.append(row);return row
            finally:
                resume.set();worker.join(5);bridge.close()

    def test_isolated_semantic_callback_cancel(self):self.cell(True,'cancel')
    def test_isolated_semantic_callback_expiry(self):self.cell(True,'expiry')
    def test_synchronous_semantic_callback_cancel_control(self):self.cell(False,'cancel')
    def test_synchronous_semantic_callback_expiry_control(self):self.cell(False,'expiry')
    def test_stable_isolated_composition(self):self.cell(True,'none')
    def test_stable_synchronous_composition(self):self.cell(False,'none')


if __name__=='__main__':unittest.main()
