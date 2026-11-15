import asyncio
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from runtime.cli_v1.test_mcp_process_identity import metadata


class PublicG10ProductionStdioTests(unittest.IsolatedAsyncioTestCase):
    async def test_public_g10_receipt_and_parent_effect_cross_stdio_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            output=root/'child-output'
            targets=root/'targets.json'
            targets.write_text(json.dumps({'app':20}),encoding='utf-8')
            params=StdioServerParameters(command=sys.executable,
                args=['-m','runtime.cli_v1.mcp_calc_g10_stdio_test_server',
                    '--output-directory',str(output),'--targets',str(targets),
                    '--session-mode','guarded-x11','--guarded-process-identity',
                    '--guarded-query-worker','--guarded-window-lifecycle',
                    '--guarded-owned-process'],
                cwd=str(Path(__file__).resolve().parents[2]))
            async with stdio_client(params) as (reader,writer):
                async with ClientSession(reader,writer) as client:
                    await client.initialize()
                    names={tool.name for tool in (await client.list_tools()).tools}
                    self.assertTrue({'interface_guarded_calc_prepare',
                        'interface_guarded_calc_launch','interface_guarded_review_window',
                        'interface_guarded_observe','interface_guarded_mint',
                        'interface_guarded_calc_compiled','interface_guarded_input',
                        'interface_verify_task','interface_close'}.issubset(names))

                    prepared=metadata(await client.call_tool(
                        'interface_guarded_calc_prepare',{
                            'attempt_id':'g10-production-stdio',
                            'profile_id':'calc-g10-two-save-v1'}))
                    self.assertEqual(prepared['status'],'prepared',prepared)
                    launched=metadata(await client.call_tool(
                        'interface_guarded_calc_launch',{
                            'prepared_call_id':prepared['call_id'],
                            'wait_for_result_ms':10000}))
                    if launched['status']=='pending':
                        launch_call_id=launched['call_id']
                        deadline=time.monotonic()+25
                        while time.monotonic()<deadline:
                            await asyncio.sleep(0.05)
                            queried=metadata(await client.call_tool(
                                'interface_results',{'call_id':launch_call_id,
                                    'include_image':False}))
                            if queried.get('status')!='pending':
                                launched=queried
                                break
                    self.assertEqual(launched['status'],'candidate_found',launched)
                    reviewed=metadata(await client.call_tool(
                        'interface_guarded_review_window',{'window_id':20}))
                    self.assertEqual(reviewed['status'],'reviewed',reviewed)
                    observed=metadata(await client.call_tool(
                        'interface_guarded_observe',{}))
                    self.assertEqual(observed['status'],'observed',observed)
                    source=observed['source']
                    aliases={}
                    for alias in ('entry','save'):
                        minted=metadata(await client.call_tool(
                            'interface_guarded_mint',{
                                'alias':f'g10_stdio_{alias}',
                                'source_sequence':source['sequence'],
                                'point':[16,31],'region_size':[24,16],
                                'freshness_ms':5000}))
                        self.assertEqual(minted['status'],'minted',minted)
                        aliases[alias]={'alias':f'g10_stdio_{alias}',
                                        'offset':minted['offset']}

                    result=metadata(await client.call_tool(
                        'interface_guarded_calc_compiled',{
                            'profile_id':'calc-g10-two-save-v1',
                            'bindings':aliases,
                            'reviewed_sequence':source['sequence'],
                            'reviewed_artifact_sha256':source['native']['artifact']['sha256'],
                            'blank_reviewed':True,
                            'attempt_id':'g10-production-stdio',
                            'prepared_call_id':prepared['call_id'],
                            'wait_for_result_ms':10000}))
                    self.assertEqual(result['profile_id'],'calc-g10-two-save-v1',result)
                    self.assertEqual(result.get('parent_task_save_custody_adoption',{}).get(
                        'status'),'adopted',result)
                    self.assertEqual(result['method_receipt']['outcome'],
                                     'TASK_SUCCEEDED',result)
                    self.assertEqual([row['action'] for row in result['task_save_receipts']],
                                     ['first','second'],result)
                    self.assertTrue(all(row['release_verified'] is True
                        for row in result['method_receipt']['transitions']),result)
                    self.assertIsNone(result['task_success'],result)
                    self.assertFalse(result['replay_allowed'],result)

                    neutral_source=metadata(await client.call_tool(
                        'interface_guarded_observe',{}))
                    neutral=metadata(await client.call_tool(
                        'interface_guarded_mint',{
                            'alias':'g10_stdio_neutral',
                            'source_sequence':neutral_source['source']['sequence'],
                            'point':[16,31],'region_size':[24,16],
                            'freshness_ms':5000}))
                    self.assertEqual(neutral['status'],'minted',neutral)
                    release_probe=metadata(await client.call_tool(
                        'interface_guarded_input',{
                            'alias':'g10_stdio_neutral','offset':neutral['offset'],
                            'interaction':'keyboard','observe_after':False,
                            'tail':[{'op':'key_chord','keys':['CTRL','a']}],
                            'wait_for_result_ms':10000}))
                    self.assertEqual(release_probe['status'],'completed',release_probe)
                    release=release_probe['result']['execution']['releases'][-1]
                    self.assertTrue(release['verified'],release_probe)
                    self.assertEqual(release['keys_down'],[],release_probe)

                    closed=metadata(await client.call_tool('interface_close',{}))
                    self.assertEqual(closed['status'],'closed',closed)
                    verified=metadata(await client.call_tool(
                        'interface_verify_task',{'call_id':result['call_id']}))
                    self.assertEqual(verified['status'],'verified',verified)
                    self.assertIs(verified['task_success'],True,verified)
                    self.assertEqual(verified['task_effect']['reason'],
                                     'both_g10_saved_effects_verified',verified)
                    self.assertFalse(verified['operation_invoked'],verified)

            artifact_root=Path(prepared['artifact_path']).parent
            saved=[artifact_root/'g10-first.fods',artifact_root/'g10-second.fods']
            self.assertTrue(all(path.is_file() for path in saved),
                            [str(path) for path in saved])
            startup=json.loads((output/'owner-get-timing.json').read_text(
                encoding='utf-8'))
            self.assertEqual(startup['outcome'],'open',startup)
            self.assertGreater(startup['elapsed_ns'],0,startup)
            print('OWNER_GET_TIMING',json.dumps(startup,sort_keys=True))


if __name__=='__main__':
    unittest.main()
