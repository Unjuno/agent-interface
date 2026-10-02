"""Independent raw-only verification. Does not import actor, runner or engine."""
import base64
import hashlib
import json
from pathlib import Path
import sys

NAMES = ('NO_CUE','VALID','OLD_GENERATION','FOREIGN_SESSION','WRONG_SURFACE',
         'FUTURE_TIME','EXPIRED_TIME','ROI_OUTSIDE','MISSING_HISTORY','AUTHORITY_FIELD')
REASONS = ('NO_CUE','ACCEPTED','GENERATION','SESSION','SURFACE',
           'TIME','TIME','ROI','ACCEPTED','SCHEMA')


def verify_case(o):
    errors, checks = [], 0
    def check(condition, reason):
        nonlocal checks
        checks += 1
        if not condition: errors.append(reason)
    try:
        name = o['scenario']; index = NAMES.index(name)
        req, ans = o['request'], o['response']
        full = o['all_frames']; current = req['current']; cue = req['cue']
        surface = o['wire'][0]['value']['surface']
        check(o['error'] is None, 'case_error')
        check(o['layout'] == {'bits_per_pixel':32,'depth':24,'image_byte_order':0,'scanline_pad':32},'layout')
        check(current == {'session':o['session'],'surface':surface,'generation':3},'current_scope')
        check(len(full)==3, 'native_frame_count')
        for i, f in enumerate(full,1):
            check(f['frame_id']==i,'frame_identity')
            check(all(f[k]==current[k] for k in current),'frame_scope')
            pixels=base64.b64decode(f['pixels_b64'],validate=True)
            expected=bytearray()
            for y in range(48):
                for x in range(64):
                    value=i*0x220000 if 32<=x<48 and 8<=y<24 else i*0x111111
                    expected.extend(value.to_bytes(4,'little'))
            check(pixels == expected,'native_render_bytes')
        check(all(full[i]['captured_ns']<full[i+1]['captured_ns'] for i in (0,1)),'capture_order')
        expected_frames=full[-1:] if name=='MISSING_HISTORY' else full
        check(req['frames']==expected_frames,'available_history')
        check(json.loads(o['engine_stdin'])==req,'request_wire')
        check(json.loads(o['engine_stdout'])==ans and o['engine_stderr']=='','response_wire')
        now=ans['checked_ns']
        check(full[-1]['captured_ns']<=o['before']['at_ns']<=now<=o['after']['at_ns']<=o['frame_after']['captured_ns'],'query_clock_order')
        check(cue is None if name=='NO_CUE' else isinstance(cue,dict),'cue_presence')
        if cue is not None:
            expected_keys={'cue_id','session','surface','generation','emitted_ns','roi'}
            if name=='AUTHORITY_FIELD': expected_keys.add('authority_granted')
            check(set(cue)==expected_keys,'cue_schema_binding')
            check(cue['cue_id']==o['session']+'-cue','cue_identity')
            check(cue['generation']==(2 if name=='OLD_GENERATION' else 3),'cue_generation')
            check(cue['session']==('other-session' if name=='FOREIGN_SESSION' else o['session']),'cue_session')
            check(cue['surface']==surface+(name=='WRONG_SURFACE'),'cue_surface')
            check(cue['roi']==([60,40,16,16] if name=='ROI_OUTSIDE' else [32,8,16,16]),'cue_roi')
            if name=='FUTURE_TIME': check(cue['emitted_ns']>now,'future_exposure')
            elif name=='EXPIRED_TIME': check(now-cue['emitted_ns']>2_000_000_000,'expiry_exposure')
            else: check(0<=now-cue['emitted_ns']<=2_000_000_000,'timely_exposure')
            if name=='AUTHORITY_FIELD': check(cue['authority_granted'] is True,'authority_injection')
        roi=[32,8,16,16] if name in ('VALID','MISSING_HISTORY') else [0,0,16,16]
        check(ans['reason']==REASONS[index],'cue_disposition')
        check(ans['roi']==roi,'selected_roi')
        check(ans['history']==('MISSING_HISTORY' if name=='MISSING_HISTORY' else 'COMPLETE'),'history_disposition')
        check(len(ans['frames'])==len(expected_frames),'output_history_count')
        check(ans['decoded_bytes']==len(expected_frames)*16*16*4<=3072,'evidence_budget')
        for raw, part in zip(expected_frames,ans['frames']):
            check(part['frame_id']==raw['frame_id'] and part['captured_ns']==raw['captured_ns'],'crop_lineage')
            pixels=base64.b64decode(raw['pixels_b64'],validate=True)
            # Independent per-pixel indexing, not the engine's row slicing.
            selected=bytes(pixels[4*(y*64+x)+c] for y in range(roi[1],roi[1]+16)
                           for x in range(roi[0],roi[0]+16) for c in range(4))
            check(base64.b64decode(part['pixels_b64'],validate=True)==selected,'crop_bytes')
        check(ans['authority_granted'] is False,'authority')
        check(ans['action'] is None,'action')
        check(ans['lease_extended'] is False,'lease')
        check(o['before']['state']==o['after']['state']==3,'task_state')
        check(o['before']['surface']==o['after']['surface']==surface,'task_surface')
        check(o['before']['input_events']==o['after']['input_events']==[],'task_input')
        check(o['frame_after']['pixels_b64']==full[-1]['pixels_b64'],'frame_unchanged')
        check(o['keymap_before']==o['keymap_after']=='00'*32,'neutral_keys')
        check(o['buttons_before']==o['buttons_after']==0,'neutral_buttons')
        sends=[w['value'] for w in o['wire'] if w['direction']=='send']
        check(sends==[{'op':'DRAW','state':i} for i in (1,2,3)]+[{'op':'INSPECT'},{'op':'INSPECT'},{'op':'CLOSE'}],'app_commands')
        receives=[w['value'] for w in o['wire'] if w['direction']=='receive']
        check(len(receives)==7 and len(o['wire'])==13,'app_wire_count')
        check(receives[4]==o['before'] and receives[5]==o['after'],'inspection_wire')
        check([v['state'] for v in receives[1:]]==[1,2,3,3,3,3],'draw_effects')
        check(all(v['input_events']==[] for v in receives[1:]),'all_app_input')
        procs={p['role']:p for p in o['processes']}
        check(set(procs)=={'actor','engine','server'} and len(o['processes'])==3,'process_coverage')
        check(all(p['returncode']==0 for p in o['processes']),'process_exits')
        check(len(set(p['pid'] for p in o['processes']))==3,'process_distinct')
        check(receives[0]['pid']==procs['actor']['pid'],'actor_pid')
        check('-auth' in procs['server']['argv'] and '-nolisten' in procs['server']['argv'],'private_server')
        check(o['socket_removed'] is True,'cleanup')
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        errors.append('malformed:'+type(exc).__name__)
    return {'checks':checks,'errors':errors}


def audit(root):
    root=Path(root); errors=[]; checks=0; rows=[]
    freeze=json.loads((root/'FREEZE.json').read_text())
    for name,digest in freeze['sha256'].items():
        checks+=1
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest: errors.append('source:'+name)
    for b in range(4):
        for suffix in ('START.json','END.json'):
            checks+=1
            if not (root/'formal'/f'b{b}'/suffix).exists(): errors.append(f'b{b}:{suffix}')
        receipt_path=root/'formal'/f'launch-{b}.json'
        checks+=1
        if not receipt_path.exists(): errors.append(f'b{b}:launch'); continue
        receipt=json.loads(receipt_path.read_text())
        if receipt.get('returncode')!=0 or receipt.get('timed_out') is not False: errors.append(f'b{b}:exit')
        for i in range(5):
            p=root/'formal'/f'b{b}'/f'c{i}'/'case.json'
            checks+=1
            if not p.exists(): errors.append(f'{b}:{i}:missing'); continue
            o=json.loads(p.read_text()); rows.append(o)
            v=verify_case(o); checks+=v['checks']; errors.extend(f'{b}:{i}:{e}' for e in v['errors'])
            if o['scenario']!=NAMES[(5*b+i)%10]: errors.append(f'{b}:{i}:schedule')
            if o['session']!=f'ac41-formal-b{b}-c{i}-r{(5*b+i)//10}': errors.append(f'{b}:{i}:session')
    metrics={}
    for name in NAMES:
        chosen=[o for o in rows if o['scenario']==name]
        metrics[name]={'cases':len(chosen),'reasons':[o.get('response',{}).get('reason') for o in chosen]}
    return {'decision':'PASS_CUE_CHANNEL_RUNG0_SCOPED' if not errors else 'HOLD_OR_FAIL_CUE_RUNG0',
            'checks':checks,'errors':errors,'sessions':len(rows),'metrics':metrics}


if __name__=='__main__':
    result=audit(sys.argv[1]); print(json.dumps(result,sort_keys=True,indent=2)); raise SystemExit(bool(result['errors']))
