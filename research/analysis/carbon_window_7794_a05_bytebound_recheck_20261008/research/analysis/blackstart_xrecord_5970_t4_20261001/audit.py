from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from Xlib import display
from Xlib.ext import record
from Xlib.protocol import rq
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
T3=REPO/'research/analysis/blackstart_source_bound_5970_t3_20261001'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    raw=json.loads((HERE/'candidate.raw.json').read_text()); run=raw['run']; errors=[]; events=[]
    expected={'app.py':'fe24b580beaf048921352cc49ec380ba6f3122240c9197a1b62fc766d72afa63','observer.py':'a3e46223019f67bf98bb2a202aa24196628d2c975255bec034bd7855bf812d4d'}
    actual={n:sha(T3/'derived'/n) for n in expected}
    if actual!=expected: errors.append('T3_DERIVED_HASH_MISMATCH')
    if raw.get('archive_sha256')!='5f153824d677503275f268e2aef9c9971d5f0a3f369c573feaa1a5d10604ad8d': errors.append('ARCHIVE_HASH_MISMATCH')
    d=display.Display()
    try:
        for block in run.get('record_blocks',[]):
            if block['category']!=record.FromServer: continue
            data=bytes.fromhex(block['data_hex'])
            if len(data)%32: errors.append('RECORD_PAYLOAD_NOT_32_BYTE_ALIGNED'); continue
            while data:
                ev,data=rq.EventField(None).parse_binary_value(data,d.display,len(data),32)
                events.append({'type':int(ev.type),'detail':int(getattr(ev,'detail',-1)),'time':int(getattr(ev,'time',-1)),'root':int(getattr(getattr(ev,'root',None),'id',0)),'event':int(getattr(getattr(ev,'event',None),'id',0))})
    finally: d.close()
    presses=[e for e in events if e['type']==2]; releases=[e for e in events if e['type']==3]
    app=run.get('app_rows',[]); obs=run.get('observer_rows',[])
    matched=(len(events)==2 and len(presses)==1 and len(releases)==1 and presses[0]['detail']==run['keycode'] and releases[0]['detail']==run['keycode'] and len(app)==2 and [r['kind'] for r in app]==['KeyPress','KeyRelease'] and all(r['keycode']==run['keycode'] for r in app) and len(obs)==0 and run['release_attempted'] and run['terminal_neutral'] is True and run['error'] is None)
    status='PASS_RECORD_DISAMBIGUATES_OBSERVER_GAP' if matched and not errors else 'HOLD_RECORD_OR_STREAM_INCOMPLETE'
    result={'schema':'blackstart-xrecord-t4-independent-audit-v1','status':status,'errors':errors,'verified_t3_sha256':actual,'record_events':events,'counts':{'record':len(events),'app':len(app),'observer':len(obs)},'release_attempted':run['release_attempted'],'terminal_neutral':run['terminal_neutral'],'record_thread_errors':run.get('record_errors',[]),'scope':'server-delivered core X events in private Xvfb only; no physical HID or causal ordering inference'}
    (HERE/'audit.raw.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True)); return 0 if matched and not errors else 2
if __name__=='__main__': raise SystemExit(main())
