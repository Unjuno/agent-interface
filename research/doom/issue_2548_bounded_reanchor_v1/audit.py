from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def sha256(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--results',type=Path,required=True); a=ap.parse_args()
    rows=json.loads(a.results.read_text()); failures=[]
    for r in rows:
        g=r['guard_only']['admission']; re=r['reanchor']['admission']
        if r['arm']=='coast' and r['id']=='c01-coast-guard-only' and g!='ADMIT': failures.append((r['id'],'guard coast not admitted'))
        if r['arm']=='recovery' and g!='REJECT_CONTEXT_CHANGED': failures.append((r['id'],'guard recovery admitted'))
        if r['id']=='c03-drift-fresh-reanchor' and re!='ADMIT': failures.append((r['id'],'fresh same-session reanchor did not admit'))
        if r['id']=='c04-coast-fresh-reanchor' and re!='ADMIT': failures.append((r['id'],'fresh unchanged did not admit'))
        if r['id'] in ('c05-stale-reanchor','c06-ambiguous-reanchor') and re not in ('REJECT_NO_FRESH_OBSERVATION','REJECT_PROVENANCE'): failures.append((r['id'],'control admitted'))
        if r['reanchor'].get('fresh_mae') is not None and r['reanchor']['fresh_mae'] < 0: failures.append((r['id'],'negative mae'))
    report={'schema':'issue-2548-audit-v1','status':'PASS' if not failures else 'FAIL','case_count':len(rows),'failures':failures,'result_sha256':sha256(a.results)}
    print(json.dumps(report,indent=2,sort_keys=True)); raise SystemExit(0 if not failures else 1)
if __name__=='__main__': main()
