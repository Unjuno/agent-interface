import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from native_exchange_v1 import encoded


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_managed_start_failure_is_retained_and_never_relaunched(self):
        with tempfile.TemporaryDirectory() as tmp:
            allocation=Path(tmp)/'allocation'
            parameters=StdioServerParameters(command=sys.executable,args=[
                str(Path(__file__).with_name('native_mcp_v1.py')),
                '--allocation-directory',str(allocation),'--app','inkscape',
                '--harness-python',str(Path(tmp)/'missing-python')],env=dict(os.environ))
            async with stdio_client(parameters) as (reader,writer):
                async with ClientSession(reader,writer) as client:
                    await client.initialize()
                    listed=await client.list_tools()
                    self.assertTrue({'native_start','native_status'} <= {t.name for t in listed.tools})
                    status=await client.call_tool('native_status',{})
                    self.assertEqual(json.loads(status.content[0].text)['allocation']['status'],'not_started')
                    first=await client.call_tool('native_start',{'timeout':0})
                    self.assertEqual(json.loads(first.content[0].text)['allocation']['status'],'needs_review')
                    original=(allocation/'launch.json').read_bytes()
                    modified=(allocation/'launch.json').stat().st_mtime_ns
                    again=await client.call_tool('native_start',{'timeout':0})
                    self.assertEqual(json.loads(again.content[0].text)['allocation']['status'],'needs_review')
                    self.assertEqual((allocation/'launch.json').read_bytes(),original)
                    self.assertEqual((allocation/'launch.json').stat().st_mtime_ns,modified)
                    rejected=await client.call_tool('native_submit',{'stage':1,'decision':{'source_sequence':1,'finish':True}})
                    self.assertTrue(rejected.isError)
                    self.assertIn('own a live ready allocation',rejected.content[0].text)
                    self.assertFalse((allocation/'run').exists())

    async def test_stdio_observe_submit_pending_resume_and_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pixels = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9xkAAAAASUVORK5CYII=')
            (root/'frame.png').write_bytes(pixels)
            source = {'sequence':1, 'capture_ns':123, 'native':{
                'sha256':'raw', 'capture_started_ns':123, 'artifact':{
                    'path':str(root/'frame.png'), 'sha256':hashlib.sha256(pixels).hexdigest(),
                    'source_raw_sha256':'raw','mime_type':'image/png'}}}
            (root/'source-1.json').write_bytes(encoded(source))
            goal = {'task':{'kind':'write_cells','cells':{'A1':190,'A2':676}}}
            (root/'goal.json').write_bytes(encoded(goal))
            (root/'exchange-contract.json').write_bytes(encoded({
                'schema':'agent-interface/native-exchange-contract-v1','max_stages':6}))
            (root/'evaluation.json').write_text('{"private_score":"DO_NOT_EXPOSE"}')
            parameters = StdioServerParameters(command=sys.executable, args=[
                str(Path(__file__).with_name('native_mcp_v1.py')), '--run-directory', tmp], env=dict(os.environ))
            async with stdio_client(parameters) as (reader, writer):
                async with ClientSession(reader, writer) as client:
                    await client.initialize()
                    listed = await client.list_tools()
                    self.assertEqual({t.name for t in listed.tools}, {'native_observe','native_submit','native_resume'})
                    schema=next(t.inputSchema for t in listed.tools if t.name=='native_submit')
                    decision_schema=schema['$defs']['NativeDecision']
                    self.assertEqual(decision_schema['required'],['source_sequence'])
                    self.assertTrue({'point','tail','expected_title','finish_after'} <= set(decision_schema['properties']))
                    for bad in [{'source_sequence':1},
                                {'source_sequence':1,'finish':'true'},
                                {'source_sequence':1,'finish':1},
                                {'source_sequence':1,'finish':True,'finish_after':True},
                                {'source_sequence':1,'point':[True,2],'expected_title':'app'},
                                {'source_sequence':1,'point':[1,2,3],'expected_title':'app'}]:
                        rejected=await client.call_tool('native_submit', {'stage':1,'decision':bad,'timeout':0})
                        self.assertTrue(rejected.isError)
                        self.assertFalse((root/'request-1.json').exists())
                    observed = await client.call_tool('native_observe', {'stage':1})
                    self.assertFalse(observed.isError)
                    self.assertEqual([b.type for b in observed.content], ['text','image'])
                    self.assertEqual(base64.b64decode(observed.content[1].data), pixels)
                    self.assertNotIn('"data":', observed.content[0].text)
                    context=json.loads(observed.content[0].text)['session_context']
                    self.assertEqual(context['goal']['value'],goal)
                    self.assertEqual(context['goal']['source']['sha256'],hashlib.sha256(encoded(goal)).hexdigest())
                    self.assertEqual(context['exchange_contract']['value']['max_stages'],6)
                    self.assertEqual(context['authority'],'none')
                    self.assertNotIn('DO_NOT_EXPOSE',observed.content[0].text)
                    (root/'goal.json').write_text('[]')
                    incomplete = await client.call_tool('native_observe', {'stage':1})
                    self.assertFalse(incomplete.isError)
                    incomplete_metadata=json.loads(incomplete.content[0].text)
                    self.assertEqual(incomplete_metadata['session_context']['goal']['status'],'needs_review')
                    self.assertEqual(base64.b64decode(incomplete.content[1].data),pixels)
                    (root/'goal.json').write_bytes(encoded(goal))
                    invalid = await client.call_tool('native_submit', {'stage':True,'decision':{},'timeout':0})
                    self.assertTrue(invalid.isError)
                    self.assertFalse((root/'request-1.json').exists())
                    decision = {'source_sequence':1,'finish':True}
                    pending = await client.call_tool('native_submit', {'stage':1,'decision':decision,'timeout':0})
                    row = json.loads(pending.content[0].text)
                    self.assertEqual(row['status'],'pending')
                    raw = (root/'request-1.json').read_bytes()
                    before = (root/'request-1.json').stat().st_mtime_ns
                    duplicate = await client.call_tool('native_submit', {'stage':1,'decision':decision,'timeout':0})
                    self.assertTrue(duplicate.isError)
                    self.assertIsNone(json.loads(duplicate.content[0].text)['program_attempted'])
                    wrong = await client.call_tool('native_resume', {'stage':1,'decision_sha256':'0'*64,'timeout':0})
                    self.assertTrue(wrong.isError)
                    (root/'reply-1.json').write_bytes(encoded({'stage':1,'status':'finished',
                        'decision_sha256':row['decision_sha256'], 'evaluation':{'success':False},
                        'observation':source}))
                    resumed = await client.call_tool('native_resume', {'stage':1,'decision_sha256':row['decision_sha256'],'timeout':0})
                    self.assertFalse(resumed.isError)
                    result = json.loads(resumed.content[0].text)
                    self.assertTrue(result['exchange']['resumed_read_only'])
                    self.assertFalse(result['outcome_summary']['evaluation_success'])
                    self.assertEqual(base64.b64decode(resumed.content[1].data),pixels)
                    self.assertEqual((root/'request-1.json').read_bytes(),raw)
                    self.assertEqual((root/'request-1.json').stat().st_mtime_ns,before)

    def test_context_errors_remain_explicit_without_scores_or_mutation(self):
        from native_mcp_v1 import session_context
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            empty=session_context(root)
            self.assertEqual(empty['goal']['status'],'unavailable')
            self.assertEqual(empty['exchange_contract']['status'],'unavailable')
            for data in [b'[]', b'{', b'{"a": NaN}']:
                (root/'goal.json').write_bytes(data)
                result=session_context(root)
                self.assertEqual(result['goal']['status'],'needs_review')
                self.assertNotIn('value',result['goal'])
                self.assertEqual((root/'goal.json').read_bytes(),data)
            (root/'exchange-contract.json').write_bytes(encoded({
                'schema':'agent-interface/native-exchange-contract-v1','max_stages':True}))
            self.assertEqual(session_context(root)['exchange_contract']['status'],'needs_review')

    def test_typed_decision_preserves_explicit_payload_without_defaults(self):
        from native_mcp_v1 import NativeDecision
        decisions=[{'source_sequence':7,'finish':True},
            {'source_sequence':1,'point':[600,378],'expected_title':'shape.svg - Inkscape',
             'tail':[{'op':'key_chord','keys':['Right'],'repeat':18}], 'finish_after':True},
            {'source_sequence':7,'point':[48,190],'expected_title':'sheet.xlsx — LibreOffice Calc',
             'interaction':'keyboard','tail':[{'op':'text','text':'190'}],
             'finish':False,'future_extension':{'literal':[1,False,None]}}]
        for decision in decisions:
            with self.subTest(decision=decision):
                parsed=NativeDecision.model_validate(decision)
                self.assertEqual(encoded(parsed.model_dump(mode='json',exclude_unset=True)),encoded(decision))


if __name__ == '__main__':
    unittest.main()
