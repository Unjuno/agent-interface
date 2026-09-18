from __future__ import annotations
import argparse, json
from pathlib import Path

ROI=48; TARGET=12; TX=18; TY=18
DIRECTIONS={'horizontal':(1,0),'vertical':(0,1),'diagonal':(1,1)}
TASK='VISUAL-INVALIDATION-ROI-TRANSLATION-ENVELOPE-A2-20260918-002'

def area(r):
    x0,y0,x1,y1=r
    return max(0,x1-x0)*max(0,y1-y0)

def clip(r):
    return (max(0,r[0]),max(0,r[1]),min(ROI,r[2]),min(ROI,r[3]))

def inter(a,b):
    return area((max(a[0],b[0]),max(a[1],b[1]),min(a[2],b[2]),min(a[3],b[3])))

def oracle(direction,d,semantic):
    ux,uy=DIRECTIONS[direction]
    a=(TX,TY,TX+TARGET,TY+TARGET)
    b=clip((TX+ux*d,TY+uy*d,TX+ux*d+TARGET,TY+uy*d+TARGET))
    aa=area(a); bb=area(b); ii=inter(a,b)
    return aa+bb-ii if semantic else aa+bb-2*ii

def audit(r):
    errs=[]
    if r.get('task')!=TASK: errs.append('task')
    if r.get('phase')=='construction':
        rows=r.get('geometry_rows',[])
        if len(rows)!=150: errs.append('geometry_row_count')
        for row in rows:
            e=oracle(row['direction'],row['d'],row['semantic_change'])
            if row.get('count')!=e or row.get('oracle_count')!=e:
                errs.append(f"geometry:{row['direction']}:{row['d']}:{row['semantic_change']}")
        if r.get('geometry_mismatches')!=[]: errs.append('embedded_geometry_mismatch')
        if r.get('scalar_batch_mismatches')!=[]: errs.append('embedded_scalar_batch_mismatch')
        if not all(x.get('equal') is True for x in r.get('scalar_batch_checks',[])): errs.append('scalar_batch_check')
        if r.get('decision')!='PASS_CONSTRUCTION_ELIGIBLE': errs.append('construction_decision')
        return {'pass':not errs,'errors':errs,'rows':len(rows),'scalar_batch_checks':len(r.get('scalar_batch_checks',[]))}
    if r.get('phase')!='characterization':
        errs.append('phase')
        return {'pass':False,'errors':errs,'cells':0}
    cells=r.get('cells',[])
    if len(cells)!=75: errs.append('cell_count')
    idx={}
    for c in cells:
        key=(c.get('direction'),c.get('d')); idx[key]=c
        if c.get('oracle_translation_count_sigma0')!=oracle(c['direction'],c['d'],False): errs.append(f'oracle_translation:{key}')
        if c.get('oracle_semantic_count_sigma0')!=oracle(c['direction'],c['d'],True): errs.append(f'oracle_semantic:{key}')
    for direction in DIRECTIONS:
        if all((direction,d) in idx for d in range(25)):
            safe=[d for d in range(1,25) if idx[(direction,d)]['fpr']<=0.01 and idx[(direction,d)]['fnr']<=0.01]
            fail=[d for d in range(1,25) if idx[(direction,d)]['fpr']>0.01]
            hard=[d for d in range(1,25) if idx[(direction,d)]['fpr']>=0.99]
            b=r.get('bounds',{}).get(direction,{})
            if b.get('last_d_fpr_le_1pct')!=(max(safe) if safe else None): errs.append(f'bound_safe:{direction}')
            if b.get('first_d_fpr_gt_1pct')!=(min(fail) if fail else None): errs.append(f'bound_fail:{direction}')
            if b.get('first_d_fpr_ge_99pct')!=(min(hard) if hard else None): errs.append(f'bound_hard:{direction}')
    return {'pass':not errs,'errors':errs,'cells':len(cells)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out'); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); out=audit(r); s=json.dumps(out,indent=2,sort_keys=True)+'\n'; print(s,end='')
    if a.out: Path(a.out).write_text(s)
    raise SystemExit(0 if out['pass'] else 5)
if __name__=='__main__': main()
