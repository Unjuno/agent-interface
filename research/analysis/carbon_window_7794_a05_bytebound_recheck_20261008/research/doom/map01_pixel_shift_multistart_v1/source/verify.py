from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(root,plan,audit_json,freeze,ledger):
    s=json.loads((root/'summary.json').read_text()); p=json.loads(plan.read_text()); a=json.loads(audit_json.read_text()); f=json.loads(freeze.read_text()); l=json.loads(ledger.read_text()); errs=[]
    ids=[c['id'] for c in p['cases']]
    if sorted(l.get('completed',{}))!=sorted(ids) or l.get('failed') or l.get('started'): errs.append('ledger_incomplete')
    if s.get('formal_case_invocations')!=16 or s.get('same_id_reruns')!=0: errs.append('formal_count')
    if len(s.get('cases',[]))!=16 or not a.get('pass') or a.get('errors'): errs.append('audit_or_count')
    for name,h in f['source_sha256'].items():
        q=plan.parent/name
        if not q.exists() or sha(q)!=h: errs.append('source_hash:'+name)
    if any(r.get('false_matched') for r in s['cases'] if r.get('kind')=='main') and s['decision']!='FAIL_PIXEL_SHIFT_MULTISTART': errs.append('false_match_decision')
    if s['decision']=='PASS_PIXEL_SHIFT_MULTISTART_SCOPED' and not all(s['gates'].values()): errs.append('pass_gate')
    print('PASS_VERIFY' if not errs else 'FAIL_VERIFY '+json.dumps(errs)); return 0 if not errs else 1
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--audit',type=Path,required=True);ap.add_argument('--freeze',type=Path,required=True);ap.add_argument('--ledger',type=Path,required=True);a=ap.parse_args();raise SystemExit(main(a.root,a.plan,a.audit,a.freeze,a.ledger))
