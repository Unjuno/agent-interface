from __future__ import annotations
import json
from pathlib import Path
from model import Candidate, Event, LifecycleError
from oracle import HistoryOracle
HERE=Path(__file__).resolve().parent

def run(seq):
    c=Candidate(); o=HistoryOracle(); outs=[]
    for e in seq:
        co=c.step(e); oo=o.step(e)
        if co!=oo or c.snapshot()!=o.snapshot():
            raise AssertionError((e,co,oo,c.snapshot(),o.snapshot()))
        outs.append(co)
    return outs,c.snapshot()

def main():
    controls=[]
    def record(name, fn):
        try: fn(); controls.append({'name':name,'pass':True})
        except Exception as exc: controls.append({'name':name,'pass':False,'error':repr(exc)})
    def single():
        outs,s=run([Event('down','o','i','F8',True),Event('up','o','i','F8',True)])
        assert outs==[('MINTED','o:g1:F8'),('RETIRED','o:g1:F8')]
    record('single_hold',single)
    def repeated():
        outs,_=run([Event('down','o','i','F8',True),Event('down','o','i','F8',True)])
        assert outs==[('MINTED','o:g1:F8'),('ACTIVE_REUSED','o:g1:F8')]
    record('repeated_down',repeated)
    def sequential():
        outs,_=run([Event('down','o','i','F8',True),Event('up','o','i','F8',True),Event('down','o','i','F8',True)])
        assert outs[-1]==('MINTED','o:g2:F8')
    record('sequential_generation',sequential)
    def unconfirmed():
        outs,s=run([Event('down','o','i','F8',False)])
        assert outs==[('UNCONFIRMED_DOWN_NO_ID',None)] and not s['active']
    record('unconfirmed_preexisting_down',unconfirmed)
    def noactive():
        outs,_=run([Event('up','o','i','F8',True)])
        assert outs==[('NO_ACTIVE',None)]
    record('up_without_generation',noactive)
    def wrong_owner():
        outs,s=run([Event('down','o','i','F8',True),Event('up','x','i','F8',True)])
        assert outs[-1]==('LINEAGE_MISMATCH',None) and s['active']
    record('wrong_owner_retirement',wrong_owner)
    def wrong_intent():
        outs,s=run([Event('down','o','i','F8',True),Event('up','o','j','F8',True)])
        assert outs[-1]==('LINEAGE_MISMATCH',None) and s['active']
    record('wrong_intent_retirement',wrong_intent)
    def wrong_key():
        outs,s=run([Event('down','o','i','F8',True),Event('up','o','i','F9',True)])
        assert outs[-1]==('NO_ACTIVE',None) and any(x[0]=='F8' for x in s['active'])
    record('wrong_key_retirement',wrong_key)
    def cleanup():
        outs,_=run([Event('down','o','i','F8',True),Event('cleanup','o','i','F8',True)])
        assert outs[-1]==('RETIRED','o:g1:F8')
    record('cleanup_retirement',cleanup)
    def duplicate_terminal():
        outs,_=run([Event('down','o','i','F8',True),Event('up','o','i','F8',True),Event('up','o','i','F8',True)])
        assert outs[-2:]==[('RETIRED','o:g1:F8'),('NO_ACTIVE',None)]
    record('duplicate_terminal',duplicate_terminal)
    def malformed():
        for obj in [Event('bogus','o','i','F8',True), Event('down','','i','F8',True)]:
            c=Candidate(); o=HistoryOracle()
            for inst in (c,o):
                try: inst.step(obj)
                except LifecycleError: pass
                else: raise AssertionError('malformed accepted')
    record('malformed_fail_closed',malformed)
    out={'task':'PHYSICAL-KEY-HOLD-ACTUATION-IDENTITY-AUDITABLE-20260918-003','controls':controls,'controls_total':len(controls),'controls_passed':sum(x['pass'] for x in controls),'passed':all(x['pass'] for x in controls)}
    (HERE/'FIXED.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main()
