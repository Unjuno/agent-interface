import asyncio
import json
import hashlib
import os
import sys
import subprocess
import tempfile
import time
import unittest
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from runtime.cli_v1.test_mcp_process_identity import metadata


class G10FailureLedgerTests(unittest.TestCase):
    def test_failed_compiled_call_retains_request_and_report_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            output=root/'attempt'
            env=os.environ.copy()
            env['AGENT_INTERFACE_G10_LEDGER_OUTPUT']=str(output)
            env.pop('AGENT_INTERFACE_G10_READ_TIMEOUT_TOOL',None)
            env['AGENT_INTERFACE_G10_FAIL_AFTER_RESPONSE']=(
                'interface_guarded_calc_compiled')
            completed=subprocess.run([sys.executable,'-m','unittest',
                'runtime.cli_v1.test_mcp_g10_production_stdio.'
                'PublicG10ProductionStdioTests.'
                'test_public_g10_receipt_and_parent_effect_cross_stdio_transport'],
                cwd=str(Path(__file__).resolve().parents[2]),env=env,
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=False)
            self.assertNotEqual(completed.returncode,0,completed.stdout.decode(
                'utf-8',errors='replace'))
            ledger=json.loads((output/'attempt-ledger.json').read_text(
                encoding='utf-8'))
            self.assertEqual(ledger['terminal_status'],'failed',ledger)
            self.assertEqual(ledger['terminal_phase'],
                'interface_guarded_calc_compiled',ledger)
            self.assertEqual(ledger['task_effect_status'],'unknown',ledger)
            self.assertIsNone(ledger['task_success'],ledger)
            compiled=next(row for row in ledger['mcp_calls']
                if row['tool']=='interface_guarded_calc_compiled')
            self.assertTrue(compiled['call_id'],compiled)
            for digest in ('request_sha256','response_sha256','report_sha256'):
                self.assertRegex(compiled[digest],r'^[0-9a-f]{64}$',compiled)

    def test_compiled_call_read_timeout_is_retained_as_unknown_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            output=root/'attempt'
            env=os.environ.copy()
            env['AGENT_INTERFACE_G10_LEDGER_OUTPUT']=str(output)
            env.pop('AGENT_INTERFACE_G10_FAIL_AFTER_RESPONSE',None)
            env['AGENT_INTERFACE_G10_READ_TIMEOUT_TOOL']=(
                'interface_guarded_calc_compiled')
            completed=subprocess.run([sys.executable,'-m','unittest',
                'runtime.cli_v1.test_mcp_g10_production_stdio.'
                'PublicG10ProductionStdioTests.'
                'test_public_g10_receipt_and_parent_effect_cross_stdio_transport'],
                cwd=str(Path(__file__).resolve().parents[2]),env=env,
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=False)
            self.assertNotEqual(completed.returncode,0,completed.stdout.decode(
                'utf-8',errors='replace'))
            ledger=json.loads((output/'attempt-ledger.json').read_text(
                encoding='utf-8'))
            self.assertEqual(ledger['terminal_status'],'failed',ledger)
            self.assertEqual(ledger['terminal_phase'],
                'interface_guarded_calc_compiled',ledger)
            self.assertEqual(ledger['task_effect_status'],'unknown',ledger)
            self.assertIsNone(ledger['task_success'],ledger)
            compiled=next(row for row in ledger['mcp_calls']
                if row['tool']=='interface_guarded_calc_compiled')
            self.assertIsNone(compiled['call_id'],compiled)
            self.assertEqual(compiled['status'],'unknown',compiled)
            self.assertIs(compiled['transport_response_received'],False,compiled)
            self.assertIs(compiled['caller_receipt_recorded'],False,compiled)
            self.assertEqual(compiled['terminal_error_type'],'McpError',compiled)
            self.assertRegex(compiled['request_sha256'],r'^[0-9a-f]{64}$',compiled)
            self.assertIsNone(compiled['response_sha256'],compiled)
            self.assertIsNone(compiled['report_sha256'],compiled)
            self.assertEqual(compiled['server_reconciliation_status'],
                'unique_exact_request_match',compiled)
            self.assertRegex(compiled['server_persisted_call_id'],
                r'^[0-9a-f]{32}$',compiled)
            self.assertRegex(compiled['server_request_sha256'],
                r'^[0-9a-f]{64}$',compiled)
            self.assertRegex(compiled['server_report_sha256'],
                r'^[0-9a-f]{64}$',compiled)
            self.assertIsNone(compiled['server_task_success'],compiled)
            self.assertIs(compiled['server_replay_allowed'],False,compiled)


class PublicG10ProductionStdioTests(unittest.IsolatedAsyncioTestCase):
    async def test_public_g10_receipt_and_parent_effect_cross_stdio_transport(self):
        retained_root=os.environ.get('AGENT_INTERFACE_G10_LEDGER_OUTPUT')
        temporary=tempfile.TemporaryDirectory() if retained_root is None else None
        call_trace=[]
        attempt_started_ns=time.monotonic_ns()
        attempt_phase='setup'
        attempt_error=None
        root=None
        ledger_path=None
        try:
            root=(Path(retained_root).absolute() if retained_root is not None
                  else Path(temporary.name))
            root.mkdir(parents=True,exist_ok=True)
            output=root/'child-output'
            ledger_path=root/'attempt-ledger.json'
            if output.exists() or ledger_path.exists():
                raise AssertionError(f'refusing to reuse evidence output: {root}')
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
                    async def invoke(name,arguments):
                        nonlocal attempt_phase
                        attempt_phase=name
                        call_started_ns=time.monotonic_ns()
                        request_sha256=hashlib.sha256(json.dumps(
                            arguments,sort_keys=True,separators=(',', ':'),
                            allow_nan=False).encode('utf-8')).hexdigest()
                        call={'tool':name,'call_id':None,
                            'queried_call_id':(arguments.get('call_id')
                                if name in ('interface_results',
                                    'interface_verify_task') else None),
                            'status':'unknown','verified':None,
                            'invocation_started':True,
                            'transport_response_received':False,
                            'caller_receipt_recorded':False,
                            'request_sha256':request_sha256,
                            'response_sha256':None,
                            'started_monotonic_ns':call_started_ns,
                            'ended_monotonic_ns':None,'elapsed_ns':None}
                        call_trace.append(call)
                        if retained_root is not None:
                            _write_attempt_snapshot(ledger_path,output,
                                call_trace,attempt_started_ns,attempt_phase,
                                'in_progress',None)
                        try:
                            read_timeout_ms=os.environ.get(
                                'AGENT_INTERFACE_G10_READ_TIMEOUT_MS','1')
                            if (os.environ.get(
                                    'AGENT_INTERFACE_G10_READ_TIMEOUT_TOOL')
                                    ==name):
                                response=await client.call_tool(name,arguments,
                                    read_timeout_seconds=timedelta(
                                        milliseconds=int(read_timeout_ms)))
                            else:
                                response=await client.call_tool(name,arguments)
                            call['transport_response_received']=True
                            row=metadata(response)
                        except BaseException as error:
                            call_ended_ns=time.monotonic_ns()
                            if not call['caller_receipt_recorded']:
                                call.update(status='unknown')
                            call.update(
                                terminal_error_type=type(error).__name__,
                                ended_monotonic_ns=call_ended_ns,
                                elapsed_ns=call_ended_ns-call_started_ns)
                            if retained_root is not None:
                                _write_attempt_snapshot(ledger_path,output,
                                    call_trace,attempt_started_ns,attempt_phase,
                                    'in_progress',None)
                            raise
                        call_ended_ns=time.monotonic_ns()
                        call_id=row.get('call_id')
                        call.update(call_id=call_id if isinstance(call_id,str)
                                else None,
                            status=row.get('status'),
                            verified=row.get('verified'),
                            caller_receipt_recorded=True,
                            response_sha256=hashlib.sha256(json.dumps(
                                row,sort_keys=True,separators=(',', ':'),
                                allow_nan=False).encode('utf-8')).hexdigest(),
                            ended_monotonic_ns=call_ended_ns,
                            elapsed_ns=call_ended_ns-call_started_ns)
                        if retained_root is not None:
                            _write_attempt_snapshot(ledger_path,output,call_trace,
                                attempt_started_ns,attempt_phase,
                                'in_progress',None)
                        if (os.environ.get(
                                'AGENT_INTERFACE_G10_FAIL_AFTER_RESPONSE')
                                ==name):
                            raise RuntimeError(
                                'requested G10 post-response failpoint for '+name)
                        if (os.environ.get('AGENT_INTERFACE_G10_FAIL_AFTER_CALL')
                                ==name):
                            raise RuntimeError('requested G10 ledger failpoint after '
                                +name)
                        return row

                    names={tool.name for tool in (await client.list_tools()).tools}
                    self.assertTrue({'interface_guarded_calc_prepare',
                        'interface_guarded_calc_launch','interface_guarded_review_window',
                        'interface_guarded_observe','interface_guarded_mint',
                        'interface_guarded_calc_compiled','interface_guarded_input',
                        'interface_verify_task','interface_close'}.issubset(names))

                    prepared=await invoke('interface_guarded_calc_prepare',{
                            'attempt_id':'g10-production-stdio',
                            'profile_id':'calc-g10-two-save-v1'})
                    self.assertEqual(prepared['status'],'prepared',prepared)
                    launched=await invoke('interface_guarded_calc_launch',{
                            'prepared_call_id':prepared['call_id'],
                            'wait_for_result_ms':10000})
                    self.assertEqual(launched['status'],'pending',launched)
                    self.assertFalse(launched['result_available'],launched)
                    self.assertEqual(launched['effect_status'],'unknown',launched)
                    self.assertIsNone(launched['task_success'],launched)
                    self.assertFalse(launched['replay_allowed'],launched)
                    launch_wait_call_id=launched['call_id']
                    deadline=time.monotonic()+25
                    while time.monotonic()<deadline:
                        await asyncio.sleep(0.05)
                        queried=await invoke('interface_results',{
                            'call_id':launch_wait_call_id,'include_image':False})
                        if queried.get('status')!='pending':
                            launched=queried
                            break
                    self.assertEqual(launched['status'],'candidate_found',launched)
                    launch_queries=[row for row in call_trace
                        if row['tool']=='interface_results']
                    self.assertTrue(launch_queries,call_trace)
                    self.assertTrue(all(row['queried_call_id']==launch_wait_call_id
                        for row in launch_queries),launch_queries)
                    self.assertEqual(launched['call_id'],launch_wait_call_id,launched)
                    reviewed=await invoke('interface_guarded_review_window',
                        {'window_id':20})
                    self.assertEqual(reviewed['status'],'reviewed',reviewed)
                    observed=await invoke('interface_guarded_observe',{})
                    self.assertEqual(observed['status'],'observed',observed)
                    source=observed['source']
                    aliases={}
                    for alias in ('entry','save'):
                        minted=await invoke('interface_guarded_mint',{
                                'alias':f'g10_stdio_{alias}',
                                'source_sequence':source['sequence'],
                                'point':[16,31],'region_size':[24,16],
                                'freshness_ms':5000})
                        self.assertEqual(minted['status'],'minted',minted)
                        aliases[alias]={'alias':f'g10_stdio_{alias}',
                                        'offset':minted['offset']}

                    result=await invoke('interface_guarded_calc_compiled',{
                            'profile_id':'calc-g10-two-save-v1',
                            'bindings':aliases,
                            'reviewed_sequence':source['sequence'],
                            'reviewed_artifact_sha256':source['native']['artifact']['sha256'],
                            'blank_reviewed':True,
                            'attempt_id':'g10-production-stdio',
                            'prepared_call_id':prepared['call_id'],
                            'wait_for_result_ms':10000})
                    self.assertEqual(result.get('profile_id'),'calc-g10-two-save-v1',result)
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

                    neutral_source=await invoke('interface_guarded_observe',{})
                    neutral=await invoke('interface_guarded_mint',{
                            'alias':'g10_stdio_neutral',
                            'source_sequence':neutral_source['source']['sequence'],
                            'point':[16,31],'region_size':[24,16],
                            'freshness_ms':5000})
                    self.assertEqual(neutral['status'],'minted',neutral)
                    release_probe=await invoke('interface_guarded_input',{
                            'alias':'g10_stdio_neutral','offset':neutral['offset'],
                            'interaction':'keyboard','observe_after':False,
                            'tail':[{'op':'key_chord','keys':['CTRL','a']}],
                            'wait_for_result_ms':10000})
                    self.assertEqual(release_probe['status'],'completed',release_probe)
                    release=release_probe['result']['execution']['releases'][-1]
                    self.assertTrue(release['verified'],release_probe)
                    self.assertEqual(release['keys_down'],[],release_probe)

                    closed=await invoke('interface_close',{})
                    self.assertEqual(closed['status'],'closed',closed)
                    verified=await invoke('interface_verify_task',
                        {'call_id':result['call_id']})
                    self.assertEqual(verified['status'],'verified',verified)
                    self.assertEqual(verified['call_id'],result['call_id'],verified)
                    self.assertEqual(verified['attempt_id'],'g10-production-stdio',verified)
                    self.assertIs(verified['task_success'],True,verified)
                    self.assertEqual(verified['task_effect']['reason'],
                                     'both_g10_saved_effects_verified',verified)
                    self.assertEqual(verified['task_effect']['call_id'],
                                     prepared['call_id'],verified)
                    self.assertEqual(verified['task_effect']['attempt_id'],
                                     verified['attempt_id'],verified)
                    self.assertFalse(verified['operation_invoked'],verified)

                    receipts=[]
                    for item in call_trace:
                        query=item['tool'] in ('interface_results','interface_verify_task')
                        receipt={'tool':item['tool'],
                                 'kind':'read_query' if query else 'retained_call',
                                 'call_id':None if query else item['call_id'],
                                 'queried_call_id':item.get('queried_call_id')
                                    or (item['call_id'] if query else None),
                                 'status':item.get('status'),
                                 'invocation_started':item.get(
                                    'invocation_started'),
                                 'transport_response_received':item.get(
                                    'transport_response_received'),
                                 'caller_receipt_recorded':item.get(
                                    'caller_receipt_recorded'),
                                 'terminal_error_type':item.get(
                                    'terminal_error_type'),
                                 'started_monotonic_ns':item['started_monotonic_ns'],
                                 'ended_monotonic_ns':item['ended_monotonic_ns'],
                                 'elapsed_ns':item['elapsed_ns'],
                                 'request_sha256':item.get('request_sha256'),
                                 'response_sha256':item.get('response_sha256'),
                                 'report_sha256':None}
                        if not query:
                            call_dir=output/item['call_id']
                            for filename,key in (('request.json','request_sha256'),
                                                 ('report.json','report_sha256')):
                                path=call_dir/filename
                                if path.is_file():
                                    receipt[key]=hashlib.sha256(path.read_bytes()).hexdigest()
                        receipts.append(receipt)
                    attempt_ended_ns=time.monotonic_ns()
                    ledger={'schema':'agent-interface/g10-public-stdio-attempt-ledger-v1',
                        'attempt_id':'g10-production-stdio',
                        'evidence_class':'fake_x_process_stdio_fixture',
                        'provider_usage_status':'unknown_unobserved_by_fixture',
                        'provider_usage':None,
                        'mcp_calls':receipts,
                        'prepare_call_id':prepared['call_id'],
                        'compiled_call_id':result['call_id'],
                        'effect_root_call_id':verified['task_effect']['call_id'],
                        'task_effect':verified['task_effect'],
                        'task_success':verified['task_success'],
                        'attempt_started_monotonic_ns':attempt_started_ns,
                        'attempt_ended_monotonic_ns':attempt_ended_ns,
                        'lifecycle_elapsed_ns':attempt_ended_ns-attempt_started_ns,
                        'input_release_verified':release['verified'],
                        'owner_close_status':closed['status'],
                        'replay_allowed':False}
                    ledger_path.write_text(json.dumps(ledger,indent=2,
                        sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
                    self.assertEqual(len(receipts),len(call_trace),ledger)
                    self.assertTrue(all(row['report_sha256'] for row in receipts
                        if row['kind']=='retained_call'),ledger)
                    self.assertTrue(all(row['report_sha256'] is None for row in receipts
                        if row['kind']=='read_query'),ledger)
                    print('ATTEMPT_LEDGER',json.dumps(ledger,sort_keys=True))

            artifact_root=Path(prepared['artifact_path']).parent
            saved=[artifact_root/'g10-first.fods',artifact_root/'g10-second.fods']
            self.assertTrue(all(path.is_file() for path in saved),
                            [str(path) for path in saved])
            startup=json.loads((output/'owner-get-timing.json').read_text(
                encoding='utf-8'))
            self.assertEqual(startup['outcome'],'open',startup)
            self.assertGreater(startup['elapsed_ns'],0,startup)
            print('OWNER_GET_TIMING',json.dumps(startup,sort_keys=True))
            attempt_phase='completed'
        except BaseException as error:
            attempt_error=f'{type(error).__name__}: {error}'
            raise
        finally:
            if retained_root is not None and root is not None and ledger_path is not None:
                prior=json.loads(ledger_path.read_text(encoding='utf-8')) \
                    if ledger_path.is_file() else {}
                release_receipt=locals().get('release')
                release_verified=(prior.get('input_release_verified') is True
                    or (isinstance(release_receipt,dict)
                        and release_receipt.get('verified') is True))
                prior.update(terminal_status=('failed' if attempt_error else 'completed'),
                    terminal_phase=attempt_phase,terminal_error=attempt_error,
                    attempt_ended_monotonic_ns=time.monotonic_ns(),
                    server_reconciliation=_reconcile_unreturned_compiled_call(
                        call_trace,output),
                    mcp_calls=_attempt_receipts(call_trace,output),
                    task_effect_status=(prior.get('task_effect') or {}).get(
                        'status','unknown'),
                    task_success=(prior.get('task_success')
                        if 'task_success' in prior else None),
                    input_release_status=('verified' if release_verified else
                        ('caller_completed_unverified' if _observed_status(
                            call_trace,'interface_guarded_input')=='completed'
                         else 'unknown')),
                    input_release_verified=(True if release_verified else None),
                    owner_close_status=(prior.get('owner_close_status')
                        if prior.get('owner_close_status') not in (None,'unknown')
                        else _observed_status(call_trace,'interface_close')),
                    owner_close_verified=_observed_verified(call_trace,
                        'interface_close'))
                prior['lifecycle_elapsed_ns']=(prior['attempt_ended_monotonic_ns']
                    -attempt_started_ns)
                ledger_path.write_text(json.dumps(prior,indent=2,sort_keys=True,
                    allow_nan=False)+'\n',encoding='utf-8')
            if temporary is not None:
                temporary.cleanup()


def _attempt_receipts(call_trace,output):
    receipts=[]
    for item in call_trace:
        query=item['tool'] in ('interface_results','interface_verify_task')
        receipt={'tool':item['tool'],'kind':'read_query' if query else 'retained_call',
            'call_id':None if query else item['call_id'],
            'queried_call_id':(item.get('queried_call_id')
                or (item['call_id'] if query else None)),
            'status':item.get('status'),
            'verified':item.get('verified'),
            'invocation_started':item.get('invocation_started'),
            'transport_response_received':item.get(
                'transport_response_received'),
            'caller_receipt_recorded':item.get('caller_receipt_recorded'),
            'terminal_error_type':item.get('terminal_error_type'),
            'started_monotonic_ns':item['started_monotonic_ns'],
            'ended_monotonic_ns':item['ended_monotonic_ns'],
            'elapsed_ns':item['elapsed_ns'],
            'request_sha256':item.get('request_sha256'),
            'response_sha256':item.get('response_sha256'),
            'server_reconciliation_status':item.get(
                'server_reconciliation_status'),
            'server_persisted_call_id':item.get('server_persisted_call_id'),
            'server_request_sha256':item.get('server_request_sha256'),
            'server_report_sha256':item.get('server_report_sha256'),
            'server_task_success':item.get('server_task_success'),
            'server_replay_allowed':item.get('server_replay_allowed'),
            'report_sha256':None}
        if not query and isinstance(item['call_id'],str):
            call_dir=output/item['call_id']
            for filename,key in (('request.json','request_sha256'),
                                 ('report.json','report_sha256')):
                path=call_dir/filename
                if path.is_file():
                    receipt[key]=hashlib.sha256(path.read_bytes()).hexdigest()
        receipts.append(receipt)
    return receipts


def _reconcile_unreturned_compiled_call(call_trace,output):
    result=[]
    if not isinstance(output,Path):
        return result
    for item in call_trace:
        if (item.get('tool')!='interface_guarded_calc_compiled'
                or item.get('call_id') is not None
                or item.get('caller_receipt_recorded') is True):
            continue
        matches=[]
        for request_path in output.glob('*/request.json'):
            try:
                request=json.loads(request_path.read_text(encoding='utf-8'))
                arguments=request.get('arguments')
                if not isinstance(arguments,dict):
                    continue
                caller_arguments=dict(arguments)
                if 'response_wait_ms' in request:
                    caller_arguments['wait_for_result_ms']=(
                        request['response_wait_ms'])
                request_digest=hashlib.sha256(json.dumps(caller_arguments,
                    sort_keys=True,separators=(',', ':'),allow_nan=False
                    ).encode('utf-8')).hexdigest()
            except (OSError,ValueError,TypeError):
                continue
            if (request.get('operation')!='guarded_calc_compiled'
                    or request_digest!=item.get('request_sha256')):
                continue
            report_path=request_path.with_name('report.json')
            if not report_path.is_file():
                continue
            try:
                report=json.loads(report_path.read_text(encoding='utf-8'))
            except (OSError,ValueError):
                continue
            matches.append((request_path,report_path,report))
        if len(matches)!=1:
            item['server_reconciliation_status']=(
                'no_exact_request_match' if not matches
                else 'ambiguous_exact_request_matches')
            item['server_candidate_count']=len(matches)
            result.append({'tool':item['tool'],
                'request_sha256':item.get('request_sha256'),
                'status':item['server_reconciliation_status'],
                'candidate_count':len(matches)})
            continue
        request_path,report_path,report=matches[0]
        item.update(server_reconciliation_status='unique_exact_request_match',
            server_persisted_call_id=request_path.parent.name,
            server_request_sha256=hashlib.sha256(
                request_path.read_bytes()).hexdigest(),
            server_report_sha256=hashlib.sha256(
                report_path.read_bytes()).hexdigest(),
            server_task_success=(report.get('task_success')
                if type(report.get('task_success')) is bool else None),
            server_replay_allowed=(report.get('replay_allowed')
                if type(report.get('replay_allowed')) is bool else None))
        result.append({'tool':item['tool'],
            'request_sha256':item.get('request_sha256'),
            'status':'unique_exact_request_match',
            'server_persisted_call_id':item['server_persisted_call_id'],
            'server_request_sha256':item['server_request_sha256'],
            'server_report_sha256':item['server_report_sha256'],
            'task_success':item['server_task_success'],
            'replay_allowed':item['server_replay_allowed']})
    return result


def _observed_status(call_trace,tool):
    rows=[row for row in call_trace if row['tool']==tool]
    if not rows or rows[-1].get('status') is None:
        return 'unknown'
    return rows[-1]['status']


def _observed_verified(call_trace,tool):
    rows=[row for row in call_trace if row['tool']==tool]
    return rows[-1].get('verified') if rows else None


def _write_attempt_snapshot(path,output,call_trace,started_ns,phase,status,error):
    ledger={'schema':'agent-interface/g10-public-stdio-attempt-ledger-v1',
        'attempt_id':'g10-production-stdio',
        'evidence_class':'fake_x_process_stdio_fixture',
        'provider_usage_status':'unknown_unobserved_by_fixture',
        'provider_usage':None,'mcp_calls':_attempt_receipts(call_trace,output),
        'attempt_started_monotonic_ns':started_ns,
        'attempt_ended_monotonic_ns':time.monotonic_ns(),
        'lifecycle_elapsed_ns':time.monotonic_ns()-started_ns,
        'terminal_status':status,'terminal_phase':phase,'terminal_error':error,
        'task_effect_status':'unknown','task_success':None,
        'input_release_status':'unknown','owner_close_status':'unknown',
        'replay_allowed':False}
    path.write_text(json.dumps(ledger,indent=2,sort_keys=True,
        allow_nan=False)+'\n',encoding='utf-8')


if __name__=='__main__':
    unittest.main()
