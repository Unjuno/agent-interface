"""Raw-only independent reconstruction. No candidate, actor, native or Xlib imports."""
from __future__ import annotations
import argparse, base64, copy, hashlib, json, struct, sys
from pathlib import Path

MODES=('PROMPT_VALID','DELAYED_UNCHANGED','DELAYED_CHANGED','PROMPT_CHANGED',
       'STALE_BEFORE_RECEIPT','BAD_DIGEST','WRONG_ID')
BUDGET=20_000_000

def exact_int(x):
    assert type(x) is int and x>=0, 'nonnegative exact integer required'
    return x

def no_duplicates(pairs):
    d={}
    for k,v in pairs:
        if k in d: raise ValueError('duplicate JSON field')
        d[k]=v
    return d

def load_text(s):
    return json.loads(s,object_pairs_hook=no_duplicates,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))

def blob(s): return base64.b64decode(s,validate=True)

def check_row(r, index, mode, construction, actor_pid):
    expected=f'{"construction" if construction else "formal"}-b{index}-{mode}'
    assert r['case_id']==expected and r['mode']==mode and exact_int(r['batch'])==index, 'case identity'
    assert r['authority'] is False and exact_int(r['model_calls'])==exact_int(r['input_calls'])==0, 'authority/calls'
    packet=blob(r['packet_b64']); size=struct.unpack('!I',packet[:4])[0]
    assert 0<size<=1024 and len(packet)==4+size+4096, 'packet size'
    m=load_text(packet[4:4+size]);pixels=packet[4+size:]
    assert set(m)=={'case_id','seq','capture_start_ns','capture_end_ns','python_return_ns','serialize_start_ns','pixel_sha256'}, 'header fields'
    for k in ('seq','capture_start_ns','capture_end_ns','python_return_ns','serialize_start_ns'):exact_int(m[k])
    assert m['seq']==1 and m['case_id']==expected+('-other' if mode=='WRONG_ID' else ''), 'header identity'
    cap=r['capture']; ts=cap['native'];assert len(ts)==6 and exact_int(cap['returncode'])==0, 'capture receipt'
    for v in ts:exact_int(v)
    assert exact_int(cap['before_py_ns'])<=ts[0]<=ts[1]<=ts[2]<=ts[3]<=exact_int(cap['after_py_ns']), 'native clock order'
    assert ts[4]<=ts[5] and (ts[1],ts[2],cap['after_py_ns'])==(m['capture_start_ns'],m['capture_end_ns'],m['python_return_ns']), 'capture binding'
    recv=exact_int(r['received_ns']);done=exact_int(r['sampled_ns']);wire_recv=exact_int(r['transport_received_ns'])
    assert m['python_return_ns']<=m['serialize_start_ns']<=wire_recv<=recv<=done, 'delivery/completion clocks'
    if mode=='STALE_BEFORE_RECEIPT':assert recv-wire_recv>=60_000_000, 'pre-receipt delay'
    else:assert recv==wire_recv, 'restamped receipt'
    actual_hash=hashlib.sha256(pixels).hexdigest()
    assert m['pixel_sha256']==('f'*64 if mode=='BAD_DIGEST' else actual_hash), 'digest condition'
    valid=mode not in ('BAD_DIGEST','WRONG_ID')
    age=recv-m['capture_start_ns']; final_age=done-m['capture_start_ns']
    old=('YIELD_INVALID' if not valid else 'FRAME_FRESH' if age<=BUDGET else 'YIELD_STALE')
    new=(old if old!='FRAME_FRESH' else 'FRESH_AT_VALIDATION_SAMPLE' if final_age<=BUDGET else 'YIELD_STALE_AT_VALIDATION')
    assert r['legacy']==old and r['candidate']==new, 'independent decision disagreement'
    assert len(r['digest'])==(0 if mode=='WRONG_ID' else 1), 'digest call count'
    if r['digest']:
        dg=r['digest'][0]
        assert recv<=exact_int(dg['entry_ns'])<=exact_int(dg['exit_ns'])<=done, 'digest clocks'
        assert dg['input_sha256']==dg['digest']==actual_hash, 'actual digest evidence'
        if mode in ('DELAYED_UNCHANGED','DELAYED_CHANGED'):
            assert dg['exit_ns']-dg['entry_ns']>=60_000_000, 'validation delay absent'
        if mode in ('DELAYED_CHANGED','PROMPT_CHANGED'):
            assert dg['entry_ns']<=exact_int(dg['paint']['start_ns'])<=exact_int(dg['paint']['end_ns'])<=dg['exit_ns'], 'paint outside digest'
            assert dg['paint']['requested_pixels']==1024 and dg['paint']['returncode']==0, 'paint result'
        else:assert 'paint' not in dg, 'unexpected paint'
    assert r['initial_paint']['requested_pixels']==0 and r['initial_paint']['returncode']==0, 'initial paint'
    assert exact_int(r['initial_paint']['start_ns'])<=exact_int(r['initial_paint']['end_ns'])<=r['before']['before_ns'], 'initial ordering'
    for side in ('before','after'):
        o=r[side];assert exact_int(o['before_ns'])<=exact_int(o['after_ns']), 'oracle clocks'
        assert o['authority'] is False and type(o['depth']) is int and o['depth']==24, 'oracle scope'
        assert len(o['keymap'])==32 and all(type(v) is int and v==0 for v in o['keymap']), 'input keys not neutral'
        assert type(o['pointer_mask']) is int and o['pointer_mask']==0, 'input pointer not neutral'
        assert len(blob(o['pixels_b64']))==4096, 'oracle pixel bytes'
    assert r['before']['after_ns']<=cap['before_py_ns'] and done<=r['after']['before_ns'], 'oracle/source ordering'
    assert blob(r['before']['pixels_b64'])==pixels==bytes((16,16,16,0))*1024, 'independent source pixels'
    changed=mode in ('PROMPT_CHANGED','DELAYED_CHANGED')
    assert blob(r['after']['pixels_b64'])==(bytes((50,50,220,0))*1024 if changed else pixels), 'independent final pixels'
    wire=r['wire'];ops=['paint','capture']+(['paint'] if changed else [])
    assert len(wire)==len(ops), 'wire denominator'
    for rec,op in zip(wire,ops):
        request=load_text(rec['request']);response=load_text(rec['response'])
        assert rec['request'].endswith('\n') and rec['response'].endswith('\n'), 'wire framing'
        assert request['op']==response['op']==op and type(response['pid']) is int and response['pid']==actor_pid, 'wire identity'
        assert exact_int(rec['before_ns'])<=exact_int(rec['received_ns']), 'wire clocks'
    q=load_text(wire[1]['request']);w=load_text(wire[1]['response'])['result']
    assert q=={'op':'capture','case_id':expected,'bad_digest':mode=='BAD_DIGEST','wrong_id':mode=='WRONG_ID'}, 'capture request'
    assert w['capture']==cap and w['packet_b64']==r['packet_b64'] and wire[1]['received_ns']==wire_recv, 'raw capture wire binding'
    assert load_text(wire[0]['response'])['result']==r['initial_paint'], 'initial paint wire binding'
    if changed: assert load_text(wire[2]['response'])['result']==r['digest'][0]['paint'], 'change wire binding'
    expected_old={'PROMPT_VALID':'FRAME_FRESH','DELAYED_UNCHANGED':'FRAME_FRESH','DELAYED_CHANGED':'FRAME_FRESH',
                  'PROMPT_CHANGED':'FRAME_FRESH','STALE_BEFORE_RECEIPT':'YIELD_STALE','BAD_DIGEST':'YIELD_INVALID','WRONG_ID':'YIELD_INVALID'}[mode]
    expected_new={'PROMPT_VALID':'FRESH_AT_VALIDATION_SAMPLE','PROMPT_CHANGED':'FRESH_AT_VALIDATION_SAMPLE',
                  'DELAYED_UNCHANGED':'YIELD_STALE_AT_VALIDATION','DELAYED_CHANGED':'YIELD_STALE_AT_VALIDATION',
                  'STALE_BEFORE_RECEIPT':'YIELD_STALE','BAD_DIGEST':'YIELD_INVALID','WRONG_ID':'YIELD_INVALID'}[mode]
    gate=(old==expected_old and new==expected_new)
    return {'case_id':expected,'mode':mode,'receipt_age_ns':age,'completion_age_ns':final_age,
            'legacy':old,'candidate':new,'pixels_changed':changed,'boundary_gate':gate}

def inspect_batch(state, rows, index, construction=False):
    errors=[];metrics=[]
    try:
        assert type(state['batch']) is int and state['batch']==index and state['construction'] is construction, 'batch identity'
        assert state['status']=='COMPLETE', 'batch incomplete'
        assert state['authority'] is False and exact_int(state['model_calls'])==exact_int(state['input_calls'])==0, 'batch authority'
        assert type(state['actor_exit']) is int and state['actor_exit']==0, 'actor exit'
        assert type(state['xvfb_exit']) is int and state['xvfb_exit']==0, 'Xvfb exit'
        assert state['xvfb_reaped'] is True and state['socket_removed'] is True and state['auth_enabled'] is True, 'cleanup/auth'
        assert exact_int(state['started_ns'])<exact_int(state['ended_ns']), 'batch clock'
        assert exact_int(state['actor_pid'])!=exact_int(state['xvfb_pid']), 'distinct processes'
        order=list(MODES[index:]+MODES[:index]);prefix='construction' if construction else 'formal'
        assert state['cases']==[f'{prefix}-b{index}-{m}' for m in order] and set(rows)==set(MODES), 'case denominator/order'
        assert load_text(state['ready_wire'])=={'event':'ready','pid':state['actor_pid']}, 'ready identity'
        qw=state['quit_wire'];assert len(qw)==1 and load_text(qw[0]['request'])=={'op':'quit'}, 'quit request'
        assert load_text(qw[0]['response'])=={'op':'quit','result':{'stopped':True},'pid':state['actor_pid']}, 'quit acknowledgement'
    except (AssertionError,KeyError,TypeError,ValueError) as exc:errors.append('batch: '+str(exc))
    for mode in MODES:
        try:metrics.append(check_row(rows[mode],index,mode,construction,state['actor_pid']))
        except (AssertionError,KeyError,TypeError,ValueError,struct.error) as exc:errors.append(mode+': '+str(exc))
    return {'errors':errors,'rows':metrics}

def from_directory(path, index, construction=False):
    state=load_text((path/'batch.json').read_text())
    rows={p.stem:load_text(p.read_text()) for p in path.glob('*.json') if p.name!='batch.json'}
    return state,rows,inspect_batch(state,rows,index,construction)

def controls(state,rows,index,construction):
    tests={
      'missing_row':lambda s,r:r.pop('BAD_DIGEST'),
      'extra_row':lambda s,r:r.update({'extra':copy.deepcopy(r['BAD_DIGEST'])}),
      'lost_exit':lambda s,r:s.pop('actor_exit'),
      'boolean_exit':lambda s,r:s.update({'actor_exit':False}),
      'authority':lambda s,r:r['PROMPT_VALID'].update({'authority':True}),
      'changed_timestamp':lambda s,r:r['DELAYED_CHANGED'].update({'sampled_ns':r['DELAYED_CHANGED']['received_ns']}),
      'false_candidate':lambda s,r:r['DELAYED_UNCHANGED'].update({'candidate':'FRESH_AT_VALIDATION_SAMPLE'}),
      'bad_legacy':lambda s,r:r['BAD_DIGEST'].update({'legacy':'FRAME_FRESH'}),
      'oracle_pixel':lambda s,r:r['PROMPT_CHANGED']['after'].update({'pixels_b64':r['PROMPT_CHANGED']['before']['pixels_b64']}),
      'missing_digest':lambda s,r:r['PROMPT_VALID'].update({'digest':[]}),
      'wrong_batch_bool':lambda s,r:r['PROMPT_VALID'].update({'batch':False}),
      'bad_wire':lambda s,r:r['PROMPT_VALID']['wire'][1].update({'response':'{}\n'})}
    result={}
    for name,mutate in tests.items():
        s=copy.deepcopy(state);r=copy.deepcopy(rows);mutate(s,r)
        result[name]=bool(inspect_batch(s,r,index,construction)['errors'])
    return result

def check_execution(receipt, consumed, state, directory, index, freeze, freeze_hash):
    assert type(receipt['index']) is int and receipt['index']==index, 'execution index'
    assert type(receipt['returncode']) is int and receipt['returncode']==0 and receipt['status']=='COMPLETE', 'external execution'
    assert receipt['freeze_sha256']==consumed['freeze_sha256']==freeze_hash, 'execution freeze'
    assert type(consumed['index']) is int and consumed['index']==index and consumed['allocation']==freeze['allocation'], 'consumed identity'
    assert type(receipt['pid']) is int and receipt['pid']==state['pid'], 'waited child identity'
    assert exact_int(consumed['started_ns'])<=exact_int(receipt['started_ns'])<=exact_int(state['started_ns'])<exact_int(state['ended_ns'])<=exact_int(receipt['ended_ns']), 'external clocks'
    command=receipt['command']
    assert len(command)==7 and command[0]==freeze['python_executable'] and command[1]=='-B', 'execution interpreter'
    assert command[2]==freeze['source_root']+'/run_batch.py' and command[3:6]==['--index',str(index),'--out'], 'execution command'
    assert command[6]==freeze['formal_root']+'/batch'+str(index), 'execution output'
    actual={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}
    assert set(receipt['evidence_sha256'])==actual, 'external manifest inventory'
    for name,h in receipt['evidence_sha256'].items():
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==h, 'raw digest '+name

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--construction',action='store_true');ap.add_argument('--controls',action='store_true');a=ap.parse_args()
    errors=[];allrows=[];corruption={}
    freeze=load_text((HERE/'FREEZE.json').read_text()) if not a.construction else None
    freeze_hash=hashlib.sha256((HERE/'FREEZE.json').read_bytes()).hexdigest() if freeze else None
    dirs=[a.root] if a.construction else [a.root/f'batch{i}' for i in range(3)]
    for i,d in enumerate(dirs):
        try:
            state,rows,result=from_directory(d,i,a.construction);errors.extend(f'b{i}:{e}' for e in result['errors']);allrows+=result['rows']
            if a.controls and i==0:corruption=controls(state,rows,i,a.construction)
            if not a.construction:
                receipt=load_text((a.root/f'batch{i}.execution.json').read_text())
                consumed=load_text((a.root/f'batch{i}.CONSUMED.json').read_text())
                check_execution(receipt,consumed,state,d,i,freeze,freeze_hash)
        except (OSError,ValueError,AssertionError,KeyError,TypeError) as exc:errors.append(f'b{i}: '+str(exc))
    if not a.construction:
        freeze=load_text((HERE/'FREEZE.json').read_text())
        for name,h in freeze['sha256'].items():
            if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=h:errors.append('source digest '+name)
    if a.controls and (len(corruption)<8 or not all(corruption.values())):errors.append('corruption controls')
    complete=len(allrows)==(7 if a.construction else 21)
    passed=complete and all(r['boundary_gate'] for r in allrows)
    decision='HOLD_EVIDENCE_INCOMPLETE' if errors else 'PASS_VALIDATION_COMPLETION_AGE_BOUNDARY_SCOPED' if passed else 'HOLD_BOUNDARY_NOT_ESTABLISHED'
    print(json.dumps({'decision':decision,'errors':errors,'rows':allrows,'corruption_controls':corruption},sort_keys=True,indent=2))
    return 0 if not errors else 2
HERE=Path(__file__).resolve().parent
if __name__=='__main__':sys.exit(main())
