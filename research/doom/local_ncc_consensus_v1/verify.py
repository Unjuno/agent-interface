"""Independent raw/result verifier: does not import model or runner."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("result"); ns=ap.parse_args()
    r=json.loads(Path(ns.result).read_text())
    errors=[]
    if r.get('formal_invocations')!=1 or r.get('formal_reruns')!=0: errors.append('invocation_count')
    rows=r.get('rows',[])
    if len(rows)!=10 or len({x.get('id') for x in rows})!=10: errors.append('denominator')
    expected={
      'rigid_p80':('rigid',80),'rigid_n70':('rigid',-70),'rigid_p165':('rigid',165),'rigid_n175':('rigid',-175),
      'parallax_a':('parallax',80),'parallax_b':('parallax',-70),'parallax_c':('parallax',25),'parallax_d':('parallax',-30)
    }
    gw=0
    for x in rows:
        if x['id'] in expected:
            kind,bg=expected[x['id']]
            if x.get('kind')!=kind or x.get('authored_background_shift')!=bg: errors.append('authored:'+x['id']); continue
            c=x.get('candidate',{})
            if c.get('status')!='IDENTIFIED' or abs(c.get('shift_px',9999)-bg)>2: errors.append('candidate:'+x['id'])
            if kind=='parallax':
                g=x.get('global',{})
                if g.get('status')=='IDENTIFIED' and abs(g.get('shift_px',9999)-bg)>2: gw+=1
        elif x['id'] in ('unrelated','low_texture'):
            if x.get('candidate',{}).get('status')=='IDENTIFIED': errors.append('control:'+x['id'])
        else: errors.append('unexpected:'+x['id'])
    expected_decision='PASS_LOCAL_NCC_CONSENSUS_SCOPED' if not errors and gw>=2 else ('HOLD_NO_PARALLAX_DISCRIMINATOR' if not errors else 'FAIL_LOCAL_CONSENSUS')
    if r.get('decision')!=expected_decision: errors.append('decision')
    print(json.dumps({'verifier':'PASS_VERIFY' if not errors else 'FAIL_VERIFY','errors':errors,'global_parallax_wrong_count':gw,'expected_decision':expected_decision},sort_keys=True))
    raise SystemExit(0 if not errors else 1)
if __name__=='__main__': main()
