import hashlib,json
from pathlib import Path
from Xlib import display
from Xlib.ext import record
from Xlib.protocol import rq
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    freeze=json.loads((HERE/'FREEZE.json').read_text()); wrapper=json.loads((HERE/'candidate.wrapper.raw.json').read_text()); run=wrapper['run']; errors=[]
    sources={n:sha(HERE/n) for n in ('candidate.py','runner.py','observer.py')}
    if sources!={n:freeze[k] for n,k in [('candidate.py','candidate_sha256'),('runner.py','runner_sha256'),('observer.py','observer_sha256')]}:errors.append('FROZEN_T6_SOURCE_HASH_MISMATCH')
    if wrapper['app_sha256']!=freeze['t3_derived_app_sha256']:errors.append('T3_APP_HASH_MISMATCH')
    d=display.Display(); records=[]
    try:
        for block in run.get('record_blocks',[]):
            if block['category']!=record.FromServer:continue
            data=bytes.fromhex(block['data_hex'])
            if len(data)%32:errors.append('RECORD_BLOCK_ALIGNMENT_ERROR');continue
            while data:
                e,data=rq.EventField(None).parse_binary_value(data,d.display,len(data),32)
                records.append({'type':int(e.type),'kind':'KeyPress' if e.type==2 else 'KeyRelease' if e.type==3 else 'other','detail':int(e.detail),'time':int(e.time),'window_xid':int(e.window.id),'root_xid':int(e.root.id)})
    finally:d.close()
    selected=set(run.get('ready',{}).get('selected_xids',[])); obs=run.get('observer_rows',[]); app=run.get('app_rows',[])
    same=(len(records)==2 and len(obs)==2 and len(app)==2 and [x['kind'] for x in records]==['KeyPress','KeyRelease'] and [x['kind'] for x in obs]==['KeyPress','KeyRelease'] and [x['kind'] for x in app]==['KeyPress','KeyRelease'] and all(r['detail']==run['keycode'] for r in records+obs+app) and [r['time'] for r in records]==[r['time'] for r in obs]==[r['time'] for r in app])
    recipient_selected=all(r['window_xid'] in selected for r in records)
    if errors:status='HOLD_FROZEN_SOURCE_OR_RAW_ERROR'
    elif run.get('release_attempted') is not True or run.get('terminal_neutral') is not True:status='HOLD_RELEASE_OR_NEUTRALITY'
    elif not same:status='HOLD_STREAMS_DIVERGE_OR_INCOMPLETE'
    elif recipient_selected:status='PASS_ALLWINDOW_CAPTURE'
    else:status='HOLD_TARGET_OUTSIDE_SELECTED_TREE'
    result={'schema':'blackstart-allwindow-trace-t6-audit-v1','status':status,'errors':errors,'source_sha256':sources,'record_events':records,'observer_events':obs,'app_events':app,'selected_xids':sorted(selected),'all_record_recipients_selected':recipient_selected,'release_attempted':run.get('release_attempted'),'terminal_neutral':run.get('terminal_neutral'),'record_errors':run.get('record_errors',[]),'scope':'single synthetic Shift pair in private Xvfb; no physical-input, production, generalized provenance, recovery or task-benefit claim'}
    (HERE/'audit.raw.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
