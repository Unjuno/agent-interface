from __future__ import annotations
import json
from pathlib import Path
from model import Candidate, Event, LifecycleError
from oracle import HistoryOracle
HERE=Path(__file__).resolve().parent

def run(seq):
    c=Candidate(); o=HistoryOracle(); outs=[]; snaps=[]
    for e in seq:
        before=c.snapshot(); co=c.step(e); oo=o.step(e); after=c.snapshot()
        if co!=oo or after!=o.snapshot(): raise AssertionError((e,co,oo,after,o.snapshot()))
        outs.append(co); snaps.append((before,after))
    return outs,c.snapshot(),snaps

def main():
    controls=[]
    def record(name,fn):
        try: fn(); controls.append({'name':name,'pass':True})
        except Exception as exc: controls.append({'name':name,'pass':False,'error':repr(exc)})
    record('single_hold',lambda: (_ for _ in ()).throw(AssertionError()) if run([Event('down','o','i','F8',True),Event('up','o','i','F8',True)])[0] != [('MINTED','o:g1:F8'),('RETIRED','o:g1:F8')] else None)
    record('repeated_down',lambda: (_ for _ in ()).throw(AssertionError()) if run([Event('down','o','i','F8',True),Event('down','o','i','F8',True)])[0][-1] != ('ACTIVE_REUSED','o:g1:F8') else None)
    record('sequential_generation',lambda: (_ for _ in ()).throw(AssertionError()) if run([Event('down','o','i','F8',True),Event('up','o','i','F8',True),Event('down','o','i','F8',True)])[0][-1] != ('MINTED','o:g2:F8') else None)
    record('unconfirmed_preexisting_down',lambda: (_ for _ in ()).throw(AssertionError()) if run([Event('down','o','i','F8',False)])[0] != [('UNCONFIRMED_DOWN_NO_ID',None)] else None)
    record('up_without_generation',lambda: (_ for _ in ()).throw(AssertionError()) if run([Event('up','o','i','F8',True)])[0] != [('NO_ACTIVE',None)] else None)
    def wrong_owner():
        outs,s,_=run([Event('down','o','i','F8',True),Event('up','x','i','F8',True)]); assert outs[-1]==('LINEAGE_MISMATCH',None) and s['active']
    record('wrong_owner_retirement',wrong_owner)
    def wrong_intent():
        outs,s,_=run([Event('down','o','i','F8',True),Event('up','o','j','F8',True)]); assert outs[-1]==('LINEAGE_MISMATCH',None) and s['active']
    record('wrong_intent_retirement',wrong_intent)
    def wrong_key():
        outs,s,_=run([Event('down','o','i','F8',True),Event('up','o','i','F9',True)]); assert outs[-1]==('NO_ACTIVE',None) and any(x[0]=='F8' for x in s['active'])
    record('wrong_key_retirement',wrong_key)
    record('cleanup_retirement',lambda: (_ for _ in ()).throw(AssertionError()) if run([Event('down','o','i','F8',True),Event('cleanup','o','i','F8',True)])[0][-1] != ('RETIRED','o:g1:F8') else None)
    record('duplicate_terminal',lambda: (_ for _ in ()).throw(AssertionError()) if run([Event('down','o','i','F8',True),Event('up','o','i','F8',True),Event('up','o','i','F8',True)])[0][-1] != ('NO_ACTIVE',None) else None)
    def malformed():
        for obj in [Event('bogus','o','i','F8',True),Event('down','','i','F8',True)]:
            for inst in (Candidate(),HistoryOracle()):
                try: inst.step(obj)
                except LifecycleError: pass
                else: raise AssertionError('malformed accepted')
    record('malformed_fail_closed',malformed)
    def known_reuse():
        outs,s,snaps=run([Event('down','o','i','F8',True),Event('down','o','i','F8',False)])
        assert outs[-1]==('ACTIVE_REUSED','o:g1:F8') and snaps[-1][0]==snaps[-1][1]
    record('unconfirmed_known_reuse',known_reuse)
    def no_active_unconfirmed():
        outs,s,snaps=run([Event('down','o','i','F8',False)])
        assert outs[-1]==('UNCONFIRMED_DOWN_NO_ID',None) and snaps[-1][0]==snaps[-1][1]
    record('unconfirmed_no_active_no_id',no_active_unconfirmed)
    out={'task':'PHYSICAL-KEY-HOLD-ACTUATION-IDENTITY-AUDITABLE-20260918-004','controls':controls,'controls_total':len(controls),'controls_passed':sum(x['pass'] for x in controls),'passed':all(x['pass'] for x in controls)}
    (HERE/'FIXED.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main()
