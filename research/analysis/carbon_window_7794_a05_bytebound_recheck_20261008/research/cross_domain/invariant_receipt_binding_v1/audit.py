from __future__ import annotations
import argparse, hashlib, json, sqlite3
from pathlib import Path
FULL={"primary":"old","collateral":"preserve"}
def canon(o): return json.dumps(o,sort_keys=True,separators=(",",":")).encode()
def sha(o): return hashlib.sha256(canon(o)).hexdigest()
def audit_case(d:Path):
    r=json.loads((d/'result.json').read_text()); receipt=json.loads((d/'contract_receipt.json').read_text())
    c=sqlite3.connect(d/'effect.sqlite'); state=dict(c.execute('SELECT k,v FROM state ORDER BY k')); ev=[(x[0],x[1],json.loads(x[2])) for x in c.execute('SELECT seq,kind,payload FROM events ORDER BY seq')]; integ=c.execute('PRAGMA integrity_check').fetchone()[0]; c.close()
    truth='EFFECT_CONTRADICTED_COMPENSATED' if state==FULL else 'EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE'
    errs=[]
    if integ!='ok' or r['integrity']!='ok': errs.append('integrity')
    if state!=r['final_state']: errs.append('state')
    if sha(receipt)!=r['receipt_sha256']: errs.append('receipt_identity')
    if [x[1] for x in ev] != ['effect','compensation']: errs.append('history')
    if r['ground_truth']!=truth or r['ground_truth_correct']!=(r['result']==truth): errs.append('truth')
    if r['policy']=='receipt_bound':
        if r['requirement_source']['kind']!='receipt' or r['requirement_source']['requirements']!=FULL: errs.append('receipt_binding')
    return {"id":r['id'],"policy":r['policy'],"scenario":r['scenario'],"pass":not errs,"errors":errs,"correct":r['ground_truth_correct']}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('evidence',type=Path); ap.add_argument('out',type=Path); a=ap.parse_args()
    rows=[audit_case(p) for p in sorted(a.evidence.iterdir()) if p.is_dir()]
    out={"schema":"invariant-receipt-binding-audit-v1","cases":len(rows),"pass":all(x['pass'] for x in rows),"correct":sum(x['correct'] for x in rows),"rows":rows}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()
