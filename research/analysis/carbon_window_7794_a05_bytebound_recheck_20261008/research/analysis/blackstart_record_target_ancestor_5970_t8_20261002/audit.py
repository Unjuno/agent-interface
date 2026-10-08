import hashlib,json
from pathlib import Path
from Xlib import display
from Xlib.ext import record
from Xlib.protocol import rq
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    f=json.loads((HERE/'FREEZE.json').read_text());wrapper=json.loads((HERE/'candidate.wrapper.raw.json').read_text());r=wrapper['run'];errors=[]
    src={n:sha(HERE/n) for n in ('candidate.py','runner.py','observer.py')}
    expected={n:f[k] for n,k in [('candidate.py','candidate_sha256'),('runner.py','runner_sha256'),('observer.py','observer_sha256')]}
    if src!=expected:errors.append('T8_SOURCE_HASH_MISMATCH')
    if wrapper.get('app_sha256')!=f['t3_derived_app_sha256']:errors.append('T3_APP_HASH_MISMATCH')
    d=display.Display();events=[]
    try:
        for b in r.get('record_blocks',[]):
            if b['category']!=record.FromServer:continue
            data=bytes.fromhex(b['data_hex'])
            if len(data)%32:errors.append('RECORD_ALIGNMENT_ERROR');continue
            while data:
                e,data=rq.EventField(None).parse_binary_value(data,d.display,len(data),32)
                events.append({'type':int(e.type),'kind':'KeyPress' if e.type==2 else 'KeyRelease' if e.type==3 else 'other','detail':int(e.detail),'time':int(e.time),'window_xid':int(e.window.id)})
    finally:d.close()
    obs=r.get('observer_rows',[]);app=r.get('app_rows',[]);selected={n['xid'] for n in r.get('ready',{}).get('windows',[]) if n.get('selected')}
    stream_match=(len(events)==len(obs)==len(app)==2 and [x['kind'] for x in events]==[x['kind'] for x in obs]==[x['kind'] for x in app]==['KeyPress','KeyRelease'] and [x['detail'] for x in events]==[x['detail'] for x in obs]==[x['detail'] for x in app]==[r['keycode']]*2 and [x['time'] for x in events]==[x['time'] for x in obs]==[x['time'] for x in app])
    recipients_selected=all(e['window_xid'] in selected for e in events)
    if errors:status='HOLD_SOURCE_OR_RAW_ERROR'
    elif r.get('release_attempted') is not True or r.get('terminal_neutral') is not True:status='HOLD_RELEASE_OR_NEUTRALITY'
    elif not stream_match:status='HOLD_OBSERVER_EMPTY_OR_DIVERGENT'
    elif not recipients_selected:status='HOLD_ANCESTOR_NOT_SELECTED'
    else:status='PASS_ANCESTOR_OBSERVER_CAPTURE'
    result={'schema':'blackstart-record-target-ancestor-t8-audit-v1','status':status,'errors':errors,'source_sha256':src,'record_events':events,'observer_events':obs,'app_events':app,'selected_xids':sorted(selected),'record_recipients_selected':recipients_selected,'release_attempted':r.get('release_attempted'),'terminal_neutral':r.get('terminal_neutral'),'record_errors':r.get('record_errors',[]),'scope':'one synthetic Shift pair in private Xvfb; no physical-input, production, general provenance, recovery, or task-benefit claim'}
    (HERE/'audit.raw.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
