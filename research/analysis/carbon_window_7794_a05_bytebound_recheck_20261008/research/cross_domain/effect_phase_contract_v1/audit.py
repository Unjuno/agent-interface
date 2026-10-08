from __future__ import annotations
import argparse,json,sqlite3
from pathlib import Path

REQ='desired'

def audit_case(d:Path):
    r=json.loads((d/'result.json').read_text())
    if r['effect_class']=='stageable':
        target=(d/'authoritative.txt').read_text().rstrip('\n')
        assert target==r['effect_value']
        if r['behavior']=='wrong':
            assert target=='old'; assert not r['effect_present']; assert r['pre_effect_reject']; assert not r['executed']
            expected_phase='REJECTED_PRE_EFFECT'
        else:
            assert target==REQ; assert r['effect_present']; assert r['executed']
            expected_phase='PUBLISHED_VERIFIED'
    else:
        con=sqlite3.connect(d/'effects.sqlite'); rows=con.execute('SELECT effect_id,value FROM effects').fetchall(); con.close()
        assert rows==[(r['id'],r['effect_value'])]
        assert r['effect_present'] and r['executed']
        if r['behavior']=='wrong':
            assert r['effect_value']=='wrong'; expected_phase='EFFECT_CONTRADICTED'
        else:
            assert r['effect_value']==REQ; expected_phase='EFFECT_VERIFIED'
    expected_verified=(r['behavior']=='correct')
    assert r['verified']==expected_verified
    assert r['phase_label']==expected_phase
    expected_legacy='COMMITTED' if expected_verified else 'REJECTED_NO_EFFECT'
    assert r['legacy_label']==expected_legacy
    legacy_no_effect_claim_correct = not (r['legacy_label']=='REJECTED_NO_EFFECT' and r['effect_present'])
    return {**r,'legacy_no_effect_claim_correct':legacy_no_effect_claim_correct,
            'phase_truth_correct': True}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    ds=sorted(p for p in a.root.iterdir() if p.is_dir() and (p/'result.json').exists())
    rows=[audit_case(d) for d in ds]
    by={}
    for r in rows:
        k=f"{r['effect_class']}:{r['behavior']}"; s=by.setdefault(k,{'n':0,'legacy_truth':0,'phase_truth':0,'effects_present':0})
        s['n']+=1; s['legacy_truth']+=int(r['legacy_no_effect_claim_correct']); s['phase_truth']+=1; s['effects_present']+=int(r['effect_present'])
    out={'schema':'effect-phase-contract-audit-v1','cases':len(rows),'by_cell':by,
         'legacy_truth_total':sum(r['legacy_no_effect_claim_correct'] for r in rows),
         'phase_truth_total':len(rows)}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
