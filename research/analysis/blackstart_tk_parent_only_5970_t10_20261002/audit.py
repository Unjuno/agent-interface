import hashlib,json
from pathlib import Path
from Xlib import display
from Xlib.ext import record
from Xlib.protocol import rq
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    f=json.loads((HERE/'FREEZE.json').read_text());w=json.loads((HERE/'candidate.wrapper.raw.json').read_text());r=w['run'];errs=[]
    t9=REPO/'research/analysis/blackstart_tk_parent_window_5970_t9_20261002';runner=t9/'runner.py';t9f=json.loads((t9/'FREEZE.json').read_text())
    if sha(HERE/'candidate.py')!=f['candidate_sha256'] or sha(HERE/'observer.py')!=f['observer_sha256'] or w.get('shared_runner_sha256')!=t9f['runner_sha256']:errs.append('SOURCE_HASH_MISMATCH')
    if w.get('app_sha256')!=f['t3_derived_app_sha256']:errs.append('APP_HASH_MISMATCH')
    d=display.Display();events=[]
    try:
        for b in r.get('record_blocks',[]):
            if b['category']!=record.FromServer:continue
            data=bytes.fromhex(b['data_hex'])
            if len(data)%32:errs.append('RECORD_ALIGNMENT_ERROR');continue
            while data:
                e,data=rq.EventField(None).parse_binary_value(data,d.display,len(data),32);events.append({'type':int(e.type),'kind':'KeyPress' if e.type==2 else 'KeyRelease' if e.type==3 else 'other','detail':int(e.detail),'time':int(e.time),'window_xid':int(e.window.id)})
    finally:d.close()
    app=r.get('app_rows',[]);obs=r.get('observer_rows',[]);selected=set(r.get('ready',{}).get('selected_xids',[]))
    exact=(len(events)==len(app)==len(obs)==2 and [e['kind'] for e in events]==[e['kind'] for e in app]==[e['kind'] for e in obs]==['KeyPress','KeyRelease'] and [e['detail'] for e in events]==[e['detail'] for e in app]==[e['detail'] for e in obs]==[r.get('keycode')]*2 and [e['time'] for e in events]==[e['time'] for e in app]==[e['time'] for e in obs])
    recipient=all(e['window_xid'] in selected for e in events)
    if errs:status='HOLD_SOURCE_OR_RAW_ERROR'
    elif r.get('release_attempted') is not True or r.get('terminal_neutral') is not True:status='HOLD_RELEASE_OR_NEUTRALITY'
    elif not exact:status='HOLD_PARENT_ONLY_STREAM_DIVERGENCE'
    elif not recipient:status='HOLD_PARENT_ONLY_TARGET_NOT_SELECTED'
    else:status='PASS_PARENT_ONLY_EXACT'
    result={'schema':'blackstart-tk-parent-only-t10-audit-v1','status':status,'errors':errs,'record_events':events,'app_events':app,'observer_events':obs,'selected_xids':sorted(selected),'recipients_selected':recipient,'release_attempted':r.get('release_attempted'),'terminal_neutral':r.get('terminal_neutral'),'record_errors':r.get('record_errors',[]),'scope':'one synthetic Shift pair in private Xvfb; no production, physical-input, general provenance, recovery or task-benefit claim'}
    (HERE/'audit.raw.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
