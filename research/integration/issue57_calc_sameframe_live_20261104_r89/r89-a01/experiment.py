import asyncio
import json
import os
import platform
import time
import traceback
from pathlib import Path
from collections import Counter

from Xlib import display
from PIL import Image
from mcp.types import TextContent
from runtime.cli_v1.mcp_server import create_server
from runtime.guarded_x11_v1.calc_launcher_v1 import CalcLaunchSupervisor

ROOT = Path(os.environ.get('EVIDENCE_DIR', '/evidence/attempt-1'))
ROOT.mkdir(parents=True, exist_ok=True)
SERVER_ROOT = ROOT / 'server-output'
SERVER_ROOT.mkdir(exist_ok=True)
RESULT = {'ocr_guard_condition':'skip', 'schema':'agent-interface/issue57-live-calc-sameframe-r89-a01',
          'mode':'live Calc exact registered Save proof and graceful clean exit',
          'input_dispatched':False,'authority_granted':False,
          'release_confirmed':None,'task_success':None,'replay_allowed':False,
          'stages':[]}

def save(name, value):
    (ROOT / name).write_text(json.dumps(value, sort_keys=True, indent=2, default=str)+'\n', encoding='utf-8')

def metadata(reply):
    if not hasattr(reply, 'content'):
        raise TypeError(f'expected MCP result, got {type(reply).__name__}')
    for block in reply.content:
        if isinstance(block, TextContent):
            try:
                return json.loads(block.text)
            except json.JSONDecodeError:
                continue
    raise ValueError('MCP response had no JSON text metadata')

async def main():
    global RESULT
    x = display.Display(os.environ['DISPLAY'])
    root_xid = x.screen().root.id
    x.close()
    RESULT['environment'] = {'platform':platform.platform(),
        'python':platform.python_version(),'display':os.environ['DISPLAY'],
        'root_xid':root_xid,'monotonic_ns':time.monotonic_ns()}
    server = create_server({'calc':root_xid}, SERVER_ROOT,
        display_name=os.environ['DISPLAY'],session_mode='guarded-x11',
        guarded_process_identity=True,guarded_query_worker=True,
        guarded_window_lifecycle=True,guarded_owned_process=True,
        _calc_launch_factory=lambda artifact: CalcLaunchSupervisor(
            '/usr/bin/soffice',custody_mode='libreoffice-oosplash-child',
            oosplash_executable='/usr/lib/libreoffice/program/oosplash',
            gui_executable='/usr/lib/libreoffice/program/soffice.bin'),
        _calc_launch_title_hint='task-artifact.fods',
        _calc_discovery_deadline_s=20.0)
    close_row=None
    input_row=None
    try:
        names=sorted(tool.name for tool in await server.list_tools())
        RESULT['public_tools']=names
        if 'interface_guarded_calc_launch' not in names:
            raise RuntimeError('public Calc launch tool was not registered')
        prep=metadata(await server.call_tool('interface_guarded_calc_prepare',
            {'attempt_id':'issue57-r89-a01'}))
        save('prepare.json',prep); RESULT['stages'].append({'prepare':prep})
        if prep.get('status')!='prepared':
            raise RuntimeError('Calc artifact preparation did not succeed')
        call_id=prep['call_id']
        launch=metadata(await server.call_tool('interface_guarded_calc_launch',
            {'prepared_call_id':call_id,'wait_for_result_ms':10000}))
        if launch.get('status')=='pending' and launch.get('call_id'):
            launch_call_id=launch['call_id']
            deadline=time.monotonic()+25
            while time.monotonic()<deadline:
                await asyncio.sleep(.25)
                observed=metadata(await server.call_tool('interface_results',
                    {'call_id':launch_call_id,'include_image':False}))
                save('launch-poll.json',observed)
                if observed.get('status')!='pending':
                    launch=observed
                    break
        save('launch.json',launch); RESULT['stages'].append({'launch':launch})
        if launch.get('status')!='candidate_found':
            raise RuntimeError('live Calc did not produce one exact-generation mapped window candidate')
        if launch.get('input_dispatched') is not False or launch.get('authority_granted') is not False:
            raise RuntimeError('launch unexpectedly reported input or authority')
        discovery=launch.get('window_discovery') or {}
        candidate=discovery.get('candidate') or {}
        xid=candidate.get('xid')
        if type(xid) is not int or xid<=1:
            raise RuntimeError('launch result omitted exact candidate XID')
        RESULT['post_launch_review_delay_s']=1.0
        await asyncio.sleep(1.0)
        reviewed=metadata(await server.call_tool('interface_guarded_review_window',
            {'window_id':xid}))
        save('review.json',reviewed); RESULT['stages'].append({'review':reviewed})
        if reviewed.get('status')!='reviewed':
            raise RuntimeError('explicit live target review failed')
        if reviewed.get('input_dispatched') is not False:
            raise RuntimeError('review unexpectedly dispatched input')
        source=reviewed.get('review',{}).get('source') or {}
        native=(source.get('native') or {})
        artifact=native.get('artifact') or {}
        image_path=Path(artifact.get('path',''))
        if not image_path.is_file() or source.get('sequence') is None:
            raise RuntimeError('review did not retain a current inspectable image source')
        with Image.open(image_path) as im:
            rgb=im.convert('RGB')
            colors=Counter(rgb.getdata())
            unique_colors=len(colors)
            dominant_rgb,dominant_count=colors.most_common(1)[0]
            dominant_fraction=dominant_count/(rgb.width*rgb.height)
            dimensions=list(rgb.size)
        surface_gate={'path':str(image_path),'sha256':artifact.get('sha256'),
            'dimensions':dimensions,'unique_rgb_colors':unique_colors,
            'dominant_rgb':list(dominant_rgb),'dominant_fraction':dominant_fraction,
            'thresholds':{'min_unique_rgb_colors':1500,'max_dominant_fraction':0.90},
            'passed':dimensions==[1280,800] and unique_colors>=1500
                and dominant_fraction<0.90}
        save('preinput-surface-gate.json',surface_gate)
        RESULT['stages'].append({'surface_gate':surface_gate})
        if not surface_gate['passed']:
            raise RuntimeError('current Calc frame failed nonblank surface gate; no input sent')
        entry=metadata(await server.call_tool('interface_guarded_mint',{
            'alias':'calc_entry','source_sequence':source['sequence'],
            'point':[16,31],'region_size':[24,16],'freshness_ms':5000}))
        save('mint-entry.json',entry); RESULT['stages'].append({'mint_entry':entry})
        if entry.get('status')!='minted': raise RuntimeError('entry anchor mint refused')
        save_binding=metadata(await server.call_tool('interface_guarded_mint',{
            'alias':'calc_save','source_sequence':source['sequence'],
            'point':[16,31],'region_size':[24,16],'freshness_ms':5000}))
        save('mint-save.json',save_binding); RESULT['stages'].append({'mint_save':save_binding})
        if save_binding.get('status')!='minted': raise RuntimeError('save toolbar anchor mint refused')
        compiled=metadata(await server.call_tool('interface_guarded_calc_compiled',{
            'profile_id':'calc-ocr-save-v1',
            'bindings':{'entry':{'alias':'calc_entry','offset':entry['offset']},
                        'save':{'alias':'calc_save','offset':save_binding['offset']}},
            'reviewed_sequence':source['sequence'],
            'reviewed_artifact_sha256':artifact.get('sha256'),
            'blank_reviewed':True,'attempt_id':'issue57-r89-a01',
            'prepared_call_id':prep['call_id'],'wait_for_result_ms':10000}))
        save('compiled-result.json',compiled); RESULT['stages'].append({'compiled':compiled})
        RESULT['compiled_call_id']=compiled.get('call_id')
        method=compiled.get('method_receipt') or {}
        transitions=method.get('transitions') or []
        RESULT['action_transition_count']=len(transitions)
        RESULT['input_dispatched']=bool(transitions)
        artifact_path=Path(prep['artifact_path'])
        from runtime.guarded_x11_v1.calc_profile_v1 import verify_saved_fods
        RESULT['independent_artifact_read_before_close']=verify_saved_fods(artifact_path)
        save('artifact-read-before-close.json',RESULT['independent_artifact_read_before_close'])
        post=metadata(await server.call_tool('interface_guarded_observe',{}))
        save('post-task-observation.json',post); RESULT['stages'].append({'post_task_observation':post})
        post_source=post.get('source') or {}
        if compiled.get('task_save_request') and post_source.get('sequence'):
            exit_ref=metadata(await server.call_tool('interface_guarded_mint',{
                'alias':'calc_exit','source_sequence':post_source['sequence'],
                'point':[83,51],'region_size':[32,24],'freshness_ms':5000}))
            save('mint-exit.json',exit_ref); RESULT['stages'].append({'mint_exit':exit_ref})
            if exit_ref.get('status')=='minted':
                exit_input=metadata(await server.call_tool('interface_guarded_input',{
                    'alias':'calc_exit','offset':exit_ref['offset'],'interaction':'keyboard',
                    'tail':[{'op':'key_chord','keys':['CTRL','q']},
                            {'op':'wait_update','timeout_ms':500}],
                    'observe_after':False,'wait_for_result_ms':10000}))
                save('graceful-quit-input.json',exit_input)
                RESULT['stages'].append({'graceful_quit_input':exit_input})
        if not isinstance(compiled.get('method_receipt'),dict):
            raise RuntimeError('compiled response omitted its method receipt')

    except BaseException as error:
        RESULT['error']={'type':type(error).__name__,'message':str(error),
                         'traceback':traceback.format_exc()}
        raise
    finally:
        try:
            close_row=metadata(await server.call_tool('interface_close',{}))
            save('close.json',close_row)
            RESULT['stages'].append({'close':close_row})
            RESULT['release_confirmed']=close_row.get('release_confirmed')
            RESULT['task_success']=close_row.get('task_success')
            RESULT['replay_allowed']=close_row.get('replay_allowed',False)
        except BaseException as error:
            RESULT['close_error']={'type':type(error).__name__,'message':str(error),
                                   'traceback':traceback.format_exc()}
        save('result.json',RESULT)
    if RESULT.get('error'):
        raise RuntimeError('live public Calc launch/review experiment failed; see result.json')
    if RESULT.get('compiled_call_id') and close_row and close_row.get('release_confirmed') is True:
        verified=metadata(await server.call_tool('interface_verify_task',{'call_id':RESULT['compiled_call_id']}))
        save('verify-task.json',verified)
        RESULT['stages'].append({'verify_task':verified})
        RESULT['task_success']=verified.get('task_success')
    save('result.json',RESULT)
    lifecycle=(close_row or {}).get('calc_target_lifecycle') or []
    if not lifecycle:
        raise RuntimeError('close report omitted Calc target lifecycle')
    cleanup=lifecycle[0].get('process_group_cleanup') or {}
    exit_receipt=lifecycle[0].get('target_process_exit_receipt') or {}
    RESULT['cleanup_summary']={'status':cleanup.get('status'),
        'verified_empty':cleanup.get('verified_empty'),
        'clean_exit_verified':cleanup.get('clean_exit_verified'),
        'target_exit_status':exit_receipt.get('status'),
        'target_exit_reason':exit_receipt.get('reason')}
    save('result.json',RESULT)
    if not (cleanup.get('verified_empty') is True
            or cleanup.get('clean_exit_verified') is True):
        raise RuntimeError('close produced neither verified-empty cleanup nor clean target exit')
    if RESULT.get('task_success') is not True:
        raise RuntimeError('parent verifier did not prove the saved Calc task effect')
    compiled_rows=[row['compiled'] for row in RESULT.get('stages',[]) if 'compiled' in row]
    method=compiled_rows[-1].get('method_receipt',{}) if compiled_rows else {}
    print(json.dumps({'method_outcome':method.get('outcome'),
        'method_reason':method.get('reason'),'task_success':RESULT.get('task_success'),
        'release_confirmed':RESULT.get('release_confirmed'),
        'cleanup':RESULT.get('cleanup_summary')},sort_keys=True))

if __name__ == '__main__':
    asyncio.run(main())







