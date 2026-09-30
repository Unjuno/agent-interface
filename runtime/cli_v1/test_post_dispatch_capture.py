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
    async def exercise(self,case='success',include_prior=True,wait_ms=None):
        with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
            capture_root=None;observed=[];dispatched=[]
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
                ex=raw['result']['execution'];ex['observations']=[dict(self.picture(Path(options['capture_directory']),'red'),operation_index=4)] if include_prior else []
                ex['releases']=[{'verified':case!='unverified','keys_down':[],'buttons_down':[],'monotonic_ns':time.monotonic_ns()}]
                ex['ended_ns']=time.monotonic_ns()
                if case=='refused':raw['result']={'status':'refused','error':'LEASE_EXPIRED','backend_emissions':0}
                if case=='recovery':session.recovery_required=True;raw['result']['recovery_required']=True
                return raw
            stack.enter_context(patch('runtime.cli_v1.mcp_server.dispatch_in_session',side_effect=dispatch))
            server=create_server({'fixture':123},td,session_mode='persistent-x11')
            reply=await server.call_tool('interface_dispatch',{'program':{},'current_observation_seq':1,
                'current_binding_revision':1,'inspect_after':'fixture','inspect_after_region':[0,0,1,1],
                'compact':True,'report_refs':True,'detail':'summary',
                **({'inspect_after_wait_ms':wait_ms} if wait_ms is not None else {})})
            self.assertFalse(reply.isError)
            row=self.row(reply)
            self.assertEqual(len(dispatched),1)
            self.assertNotIn('inspect_after_region',dispatched[0])
            self.assertNotIn('inspect_after_wait_ms',dispatched[0])
            self.assertEqual(row['session']['binding_revision'],1)
            self.assertFalse(row['authority']!='none')
            self.assertFalse(row['post_dispatch_inspection']['authority_granted'])
            original=Path(row['call_directory'],'report.json').read_bytes()
            retained=await server.call_tool('interface_results',{'call_id':row['call_id'],'include_image':True,'compact':True,'report_refs':True})
            self.assertFalse(self.row(retained)['operation_invoked'])
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
                self.assertGreaterEqual(wait['ended_ns']-wait['started_ns'],wait_ms*1_000_000)
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
    async def test_program_without_inline_observe_gets_post_release_image(self):
        await self.exercise(include_prior=False)
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
            with self.subTest(args=args),tempfile.TemporaryDirectory() as td,patch('runtime.cli_v1.mcp_session.open_session') as opened,patch('runtime.cli_v1.mcp_server.dispatch_in_session') as dispatch:
                server=create_server({'fixture':123},td,session_mode='persistent-x11')
                reply=await server.call_tool('interface_dispatch',dict(program={},current_observation_seq=1,current_binding_revision=1,**args))
                self.assertTrue(reply.isError);opened.assert_not_called();dispatch.assert_not_called()
    async def test_invalid_post_capture_rejects_before_session_or_input(self):
        for mode,target,region in [('one-shot','fixture',[0,0,1,1]),('persistent-x11',None,[0,0,1,1]),('persistent-x11','missing',[0,0,1,1]),('persistent-x11','fixture',[0,0,0,1]),('persistent-x11','fixture',[0,0,True,1]),('persistent-x11','fixture',[0,0,8192,8192])]:
            with self.subTest(mode=mode,target=target,region=region),tempfile.TemporaryDirectory() as td,patch('runtime.cli_v1.mcp_session.open_session') as opened,patch('runtime.cli_v1.mcp_server.dispatch_in_session') as dispatch:
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
