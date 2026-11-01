"""Catch pre-release image selection, repeated capture and input-after-error bugs."""
import asyncio,base64,copy,hashlib,json,tempfile,time,unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from PIL import Image
from runtime.cli_v1.mcp_server import create_server

class PostDispatchCaptureTests(unittest.IsolatedAsyncioTestCase):
    def row(self,reply):return json.loads(reply.content[0].text)
    def picture(self,root,color):
        root.mkdir(parents=True,exist_ok=True);path=root/(color+'.png')
        rgb={'red':b'\xff\x00\x00','green':b'\x00\xff\x00'}[color]
        Image.new('RGB',(1,1),tuple(rgb)).save(path);b=path.read_bytes()
        return {'bytes':3,'sha256':hashlib.sha256(rgb).hexdigest(),'width':1,'height':1,
            'target':'fixture','native_window_id':123,'frame':'screen_physical_px','region':[0,0,1,1],
            'capture_started_ns':time.monotonic_ns(),'capture_ended_ns':time.monotonic_ns(),
            'artifact':{'mime_type':'image/png','path':str(path),'bytes':len(b),
                'sha256':hashlib.sha256(b).hexdigest(),'source_raw_sha256':hashlib.sha256(rgb).hexdigest(),
                'width':1,'height':1}}
    async def exercise(self,case='success',include_prior=True,wait_ms=None,expect_summary=False):
        with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
            source_fixture=json.loads((Path(__file__).parent/'fixtures/nonpaced_dispatch_review.json').read_text())['receipt']['source']['raw_report']
            request_program=copy.deepcopy(source_fixture['normalization']['source_program']) if expect_summary else {}
            if expect_summary:request_program['ops']=[op for op in request_program['ops'] if op['op']!='observe']
            capture_root=None;observed=[];dispatched=[];wait_durations=[]
            if wait_ms is not None and case=='success':
                actual_sleep=time.sleep
                def measured_sleep(seconds):
                    started=time.perf_counter_ns()
                    actual_sleep(seconds)
                    wait_durations.append((seconds,time.perf_counter_ns()-started))
                stack.enter_context(patch('runtime.cli_v1.mcp_session.time.sleep',side_effect=measured_sleep))
            if case=='wait_error':stack.enter_context(patch('runtime.cli_v1.mcp_session.time.sleep',side_effect=OSError('interrupted settling wait')))
            def configure(directory):
                nonlocal capture_root
                capture_root=Path(directory)
            def capture(target,frame,region):
                observed.append((target,frame,region))
                if case=='capture_error':raise OSError('unavailable')
                obs=self.picture(capture_root,'green')
                return obs
            backend=SimpleNamespace(configure_capture_artifacts=configure,observe_read_only=capture,
                release_all=Mock(return_value={'verified':True,'keys_down':[],'buttons_down':[]}),close=Mock())
            session=SimpleNamespace(backend=backend,recovery_required=False)
            evidence={'window_id':123,'transient_chain':[123]}
            stack.enter_context(patch('runtime.cli_v1.mcp_session.select_backend',return_value=SimpleNamespace(available=True,backend_id='x11-v1')))
            stack.enter_context(patch('runtime.cli_v1.mcp_session.open_session',return_value=session))
            inspect=stack.enter_context(patch('runtime.cli_v1.mcp_session.inspect_focused_target',return_value=evidence))
            if case=='changed':inspect.side_effect=[evidence,dict(evidence,window_id=456)]
            def dispatch(_session,program,**options):
                dispatched.append(options)
                raw=copy.deepcopy(json.loads((Path(__file__).parent/'fixtures/nonpaced_dispatch_review.json').read_text())['receipt']['source']['raw_report'])
                ex=raw['result']['execution']
                # Translate historical fixture times into this mocked execution's
                # clock domain; mixing its old uptime with current release/capture
                # makes a legitimate summary correctly fall back on fresh hosts.
                shift=time.monotonic_ns()-200_000_000-ex['started_ns']
                ex['started_ns']+=shift
                for wait in ex['waits']:
                    wait['started_ns']+=shift;wait['ended_ns']+=shift
                ex['observations']=[dict(self.picture(Path(options['capture_directory']),'red'),operation_index=4)] if include_prior else []
                ex['releases']=[{'verified':case!='unverified','keys_down':[],'buttons_down':[],'monotonic_ns':time.monotonic_ns()}]
                ex['ended_ns']=time.monotonic_ns()
                if expect_summary:
                    raw.pop('normalization',None)
                    ex['completed_ops']=list(range(len(request_program['ops'])))
                if case=='refused':raw['result']={'status':'refused','error':'LEASE_EXPIRED','backend_emissions':0}
                if case=='recovery':session.recovery_required=True;raw['result']['recovery_required']=True
                return raw
            stack.enter_context(patch('runtime.cli_v1.api.dispatch_in_session',side_effect=dispatch))
            server=create_server({'fixture':123},td,session_mode='persistent-x11')
            reply=await server.call_tool('interface_dispatch',{'program':request_program,'current_observation_seq':1,
                'current_binding_revision':1,'inspect_after':'fixture','inspect_after_region':[0,0,1,1],
                'compact':True,'report_refs':True,'detail':'summary',
                **({'inspect_after_wait_ms':wait_ms} if wait_ms is not None else {})})
            self.assertFalse(reply.isError)
            row=self.row(reply)
            if expect_summary:
                self.assertEqual(row['receipt']['schema'],'agent-interface/receipt-view-dispatch-summary-v1')
                self.assertNotIn('raw_report',row['receipt']['source'])
            self.assertEqual(len(dispatched),1)
            self.assertNotIn('inspect_after_region',dispatched[0])
            self.assertNotIn('inspect_after_wait_ms',dispatched[0])
            self.assertEqual(row['session']['binding_revision'],1)
            self.assertFalse(row['authority']!='none')
            self.assertFalse(row['post_dispatch_inspection']['authority_granted'])
            original=Path(row['call_directory'],'report.json').read_bytes()
            retained=await server.call_tool('interface_results',{'call_id':row['call_id'],'include_image':True,'compact':True,'report_refs':True})
            self.assertFalse(self.row(retained)['operation_invoked'])
            if expect_summary:
                self.assertIn('raw_report',self.row(retained)['receipt']['source'])
                self.assertEqual(self.row(retained)['retained_call']['arguments']['program'],request_program)
                projected=await server.call_tool('interface_results',{'call_id':row['call_id'],'include_image':True,'compact':True,'report_refs':True,'detail':'summary'})
                self.assertEqual(self.row(projected)['receipt']['schema'],'agent-interface/receipt-view-dispatch-summary-v1')
                self.assertEqual(projected.content[1].data,reply.content[1].data)
                from .public_summary import summarize_public_dispatch
                full=self.row(retained)
                self.assertEqual(summarize_public_dispatch(full),full)
                wrong=copy.deepcopy(request_program);wrong['ops'].insert(-1,{'op':'wait_update','timeout_ms':1})
                self.assertEqual(summarize_public_dispatch(full,source_program=wrong),full)
                for mutation in ['early_capture','wrong_image','wait_failed','wait_extension']:
                    broken=copy.deepcopy(full)
                    context=broken['post_dispatch_inspection']
                    if mutation=='early_capture':context['observation_report']['observation']['capture_started_ns']=0
                    if mutation=='wrong_image':broken['image_reference']['post_dispatch_observation_id']='other'
                    if mutation=='wait_failed':context['capture_wait']['completed']=False
                    if mutation=='wait_extension':context['capture_wait']['error']='unrecognized'
                    broken['receipt']['source']['raw_report']['post_dispatch_inspection']=copy.deepcopy(context)
                    self.assertEqual(summarize_public_dispatch(broken,source_program=request_program),broken,mutation)
            self.assertEqual(Path(row['call_directory'],'report.json').read_bytes(),original)
            self.assertEqual(row['post_dispatch_inspection'],self.row(retained)['post_dispatch_inspection'])
            self.assertEqual([c.data for c in reply.content if c.type=='image'],[c.data for c in retained.content if c.type=='image'])
            self.assertEqual(row.get('image_reference'),self.row(retained).get('image_reference'))
            if case in ['success','capture_error','changed']:
                self.assertEqual(observed,[('fixture','screen_physical_px',[0,0,1,1])])
            else:self.assertEqual(observed,[])
            raw=json.loads(original);context=row['post_dispatch_inspection']
            if wait_ms is not None and case=='success':
                wait=context['capture_wait']
                self.assertEqual(wait['requested_ms'],wait_ms)
                self.assertTrue(wait['completed'])
                self.assertIsNone(wait['update_observed'])
                self.assertGreaterEqual(wait['started_ns'],raw['result']['execution']['releases'][0]['monotonic_ns'])
                self.assertGreaterEqual(wait['ended_ns'],wait['started_ns'])
                self.assertEqual(len(wait_durations),1)
                self.assertEqual(wait_durations[0][0],wait_ms/1000)
                self.assertGreaterEqual(wait_durations[0][1],wait_ms*1_000_000)
                self.assertGreaterEqual(context['observation_report']['observation']['capture_started_ns'],wait['ended_ns'])
            elif case=='wait_error':
                self.assertFalse(context['capture_wait']['completed'])
                self.assertIsNone(context['capture_wait']['update_observed'])
                self.assertIn('ended_ns',context['capture_wait'])
                self.assertNotIn('observation_report',context)
            elif case!='success':self.assertNotIn('capture_wait',context)
            if case=='success':
                self.assertEqual(row['image_reference']['post_dispatch_observation_id'],context['observation_report']['observation_id'])
                self.assertNotIn('execution_observation_index',row['image_reference'])
                self.assertGreaterEqual(context['observation_report']['observation']['capture_started_ns'],raw['result']['execution']['releases'][0]['monotonic_ns'])
                b=base64.b64decode(next(c.data for c in reply.content if c.type=='image'))
                import io
                self.assertEqual(Image.open(io.BytesIO(b)).getpixel((0,0)),(0,255,0))
            elif case in ['capture_error','changed','wait_error']:
                self.assertIn('error',context)
                self.assertNotIn('review_request',context)
                if case=='changed':self.assertEqual(context['recheck_evidence']['window_id'],456)
                self.assertNotIn('post_dispatch_observation_id',row['image_reference'])
                b=base64.b64decode(next(c.data for c in reply.content if c.type=='image'))
                import io
                self.assertEqual(Image.open(io.BytesIO(b)).getpixel((0,0)),(255,0,0))
            else:
                self.assertEqual(context['status'],'skipped')
            await server.call_tool('interface_close',{})
    async def test_success_delivers_after_release_image_and_lookup_never_recaptures(self):
        await self.exercise()
    async def test_no_inline_capture_summary_keeps_image_and_full_program_retrieval(self):
        await self.exercise(include_prior=False,wait_ms=20,expect_summary=True)
        # A fresh CI host has much less uptime than the frozen fixture host.
        real_clock=time.monotonic_ns;origin=real_clock()
        with self.subTest(clock='fresh-host'),patch('time.monotonic_ns',side_effect=lambda:20_000_000_000+real_clock()-origin):
            await self.exercise(include_prior=False,wait_ms=20,expect_summary=True)
    async def test_program_without_inline_observe_gets_post_release_image(self):
        await self.exercise(include_prior=False)
    async def test_wait_duration_survives_a_coarse_receipt_clock(self):
        # A nanosecond-valued receipt does not imply nanosecond resolution.
        with patch('time.monotonic_ns',return_value=20_000_000_000):
            await self.exercise(wait_ms=1)
    async def test_wait_receipt_records_actual_clock_reads_on_success_and_error(self):
        from runtime.cli_v1.mcp_session import MCPSessionOwner
        # Endpoint provenance is separate from the measured-sleep minimum.
        # Equal readings are legitimate on a coarse clock; each boundary must
        # still sample it, including the finally path after an interrupted wait.
        for ticks in [(100,200,700,900),(100,100,100,100)]:
            for interrupted in [False,True]:
                with self.subTest(ticks=ticks,interrupted=interrupted):
                    events=[];readings=iter(ticks)
                    def clock():
                        value=next(readings);events.append(('clock',value));return value
                    def sleep(seconds):
                        events.append(('sleep',seconds))
                        if interrupted:raise OSError('interrupted settling wait')
                    def inspect(*args,**kwargs):
                        events.append(('inspect',));return {'status':'needs_review'}
                    owner=MCPSessionOwner({'fixture':123})
                    owner.state='open';owner.session=SimpleNamespace(recovery_required=False)
                    report={'result':{'status':'completed','recovery_required':False,
                        'execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}}}
                    with patch('runtime.cli_v1.mcp_session.time.monotonic_ns',side_effect=clock),\
                         patch('runtime.cli_v1.mcp_session.time.sleep',side_effect=sleep),\
                         patch.object(owner,'inspect_target',side_effect=inspect) as observed:
                        context=owner.inspect_after_dispatch(report,'fixture',screen_region=[0,0,1,1],wait_ms=20)
                    wait=context['capture_wait']
                    self.assertEqual(wait,{'requested_ms':20,'started_ns':ticks[1],
                        'completed':not interrupted,'update_observed':None,'ended_ns':ticks[2]})
                    self.assertEqual((context['started_ns'],context['ended_ns']),(ticks[0],ticks[3]))
                    expected=[('clock',ticks[0]),('clock',ticks[1]),('sleep',.02),('clock',ticks[2])]
                    if not interrupted:expected.append(('inspect',))
                    expected.append(('clock',ticks[3]))
                    self.assertEqual(events,expected)
                    self.assertFalse(context['input_dispatched']);self.assertFalse(context['authority_granted'])
                    if interrupted:
                        observed.assert_not_called();self.assertIn('interrupted settling wait',context['error'])
                    else:observed.assert_called_once_with('fixture',screen_region=[0,0,1,1],capture_directory=None)
    async def test_refusal_unverified_release_and_recovery_skip_post_capture(self):
        for case in ['refused','unverified','recovery']:
            with self.subTest(case=case):await self.exercise(case)
    async def test_capture_failure_or_changed_target_preserves_original_input_image(self):
        for case in ['capture_error','changed']:
            with self.subTest(case=case):await self.exercise(case)
    async def test_explicit_wait_is_after_release_and_retained_lookup_never_waits_again(self):
        await self.exercise(wait_ms=20)
        await self.exercise('wait_error',wait_ms=20)
        for case in ['refused','unverified','recovery']:
            with self.subTest(case=case):await self.exercise(case,wait_ms=20)
    async def test_invalid_wait_rejects_before_session_or_input(self):
        for args in [{'inspect_after_wait_ms':10},{'inspect_after':'fixture','inspect_after_wait_ms':10},{'inspect_after':'fixture','inspect_after_region':[0,0,1,1],'inspect_after_wait_ms':-1},{'inspect_after':'fixture','inspect_after_region':[0,0,1,1],'inspect_after_wait_ms':1001}]:
            with self.subTest(args=args),tempfile.TemporaryDirectory() as td,patch('runtime.cli_v1.mcp_session.open_session') as opened,patch('runtime.cli_v1.api.dispatch_in_session') as dispatch:
                server=create_server({'fixture':123},td,session_mode='persistent-x11')
                reply=await server.call_tool('interface_dispatch',dict(program={},current_observation_seq=1,current_binding_revision=1,**args))
                self.assertTrue(reply.isError);opened.assert_not_called();dispatch.assert_not_called()
    async def test_invalid_post_capture_rejects_before_session_or_input(self):
        for mode,target,region in [('one-shot','fixture',[0,0,1,1]),('persistent-x11',None,[0,0,1,1]),('persistent-x11','missing',[0,0,1,1]),('persistent-x11','fixture',[0,0,0,1]),('persistent-x11','fixture',[0,0,True,1]),('persistent-x11','fixture',[0,0,8192,8192])]:
            with self.subTest(mode=mode,target=target,region=region),tempfile.TemporaryDirectory() as td,patch('runtime.cli_v1.mcp_session.open_session') as opened,patch('runtime.cli_v1.api.dispatch_in_session') as dispatch:
                server=create_server({'fixture':123},td,session_mode=mode)
                args={'program':{},'current_observation_seq':1,'current_binding_revision':1,'inspect_after_region':region}
                if target is not None:args['inspect_after']=target
                if any(type(v) is not int for v in region):
                    from mcp.server.fastmcp.exceptions import ToolError
                    with self.assertRaises(ToolError):
                        await server.call_tool('interface_dispatch',args)
                else:
                    reply=await server.call_tool('interface_dispatch',args)
                    self.assertTrue(reply.isError)
                opened.assert_not_called();dispatch.assert_not_called()

if __name__=='__main__':unittest.main()
