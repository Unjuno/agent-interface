import hashlib,json
from pathlib import Path
from Xlib.ext import record
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    f=json.loads((HERE/'FREEZE.json').read_text());w=json.loads((HERE/'candidate.wrapper.raw.json').read_text());r=w['run'];errs=[]
    if sha(HERE/'candidate.py')!=f['candidate_sha256'] or sha(HERE/'runner.py')!=f['runner_sha256']:errs.append('T12_SOURCE_HASH_MISMATCH')
    if w.get('app_sha256')!=f['t3_derived_app_sha256'] or w.get('observer_sha256')!=f['t10_parent_only_observer_sha256']:errs.append('SHARED_SOURCE_HASH_MISMATCH')
    rows=[]
    for b in r.get('record_blocks',[]):
        if b['category']!=record.FromServer:continue
        data=bytes.fromhex(b['data_hex'])
        if len(data)%32:errs.append('RECORD_ALIGNMENT_ERROR');continue
        rows.extend([{'type':data[i],'detail':data[i+1]} for i in range(0,len(data),32)])
    neutral=(r.get('initial_neutral')=={'a':True,'Shift_L':True} and r.get('terminal_neutral')=={'a':True,'Shift_L':True})
    if errs:status='HOLD_SOURCE_OR_RAW_ERROR'
    elif r.get('input_dispatched') is not False:status='HOLD_INPUT_BOUNDARY'
    elif not neutral:status='HOLD_KEYMAP_NOT_NEUTRAL'
    elif rows or r.get('observer_rows'):status='FAIL_BACKGROUND_KEY_EVENT_PRESENT'
    elif r.get('error') is not None:status='HOLD_CANDIDATE_ERROR'
    else:status='PASS_EMPTY_NO_INPUT_BASELINE'
    result={'schema':'blackstart-x11-noinput-baseline-t12-audit-v1','status':status,'errors':errs,'input_dispatched':r.get('input_dispatched'),'baseline_seconds':r.get('baseline_seconds'),'record_event_headers':rows,'observer_rows':r.get('observer_rows',[]),'initial_neutral':r.get('initial_neutral'),'terminal_neutral':r.get('terminal_neutral'),'scope':'no-input 500 ms private-Xvfb baseline only; does not adjudicate event semantics under input'}
    (HERE/'audit.raw.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
