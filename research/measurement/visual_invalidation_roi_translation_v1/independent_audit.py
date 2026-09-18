from __future__ import annotations
import argparse, json
from pathlib import Path

ROI=48
TARGET=12
ROI_X=104
ROI_Y=104
TARGET_X=ROI_X+18
TARGET_Y=ROI_Y+18
DIRECTIONS={'horizontal':(1,0),'vertical':(0,1),'diagonal':(1,1)}
TASK='VISUAL-INVALIDATION-ROI-TRANSLATION-ENVELOPE-20260918-001'

def intersect_area(a,b):
    ax0,ay0,ax1,ay1=a; bx0,by0,bx1,by1=b
    w=max(0,min(ax1,bx1)-max(ax0,bx0)); h=max(0,min(ay1,by1)-max(ay0,by0))
    return w*h

def clipped_area(r):
    roi=(ROI_X,ROI_Y,ROI_X+ROI,ROI_Y+ROI)
    return intersect_area(r,roi)

def expected(direction,d,semantic):
    ux,uy=DIRECTIONS[direction]
    a=(TARGET_X,TARGET_Y,TARGET_X+TARGET,TARGET_Y+TARGET)
    b=(TARGET_X+ux*d,TARGET_Y+uy*d,TARGET_X+ux*d+TARGET,TARGET_Y+uy*d+TARGET)
    aa=clipped_area(a); bb=clipped_area(b)
    inter_rect=(max(a[0],b[0]),max(a[1],b[1]),min(a[2],b[2]),min(a[3],b[3]))
    inter=clipped_area(inter_rect) if inter_rect[2]>inter_rect[0] and inter_rect[3]>inter_rect[1] else 0
    return aa+bb-inter if semantic else aa+bb-2*inter

def audit_construction(r):
    errs=[]
    if r.get('task')!=TASK or r.get('phase')!='construction': errs.append('identity')
    for row in r.get('noise_free_rows',[]):
        e=expected(row['direction'],row['d'],row['semantic_change'])
        if row.get('count')!=e or row.get('oracle_count')!=e:
            errs.append(f"count:{row['direction']}:{row['d']}:{row['semantic_change']}")
    if r.get('mismatches')!=[]: errs.append('embedded_mismatch')
    return {'pass':not errs,'errors':errs,'rows':len(r.get('noise_free_rows',[]))}

def audit_characterization(r):
    errs=[]
    if r.get('task')!=TASK or r.get('phase')!='characterization': errs.append('identity')
    cells=r.get('cells',[])
    if len(cells)!=75: errs.append('cell_count')
    for c in cells:
        e0=expected(c['direction'],c['d'],False); e1=expected(c['direction'],c['d'],True)
        if c.get('oracle_translation_only_count_sigma0')!=e0: errs.append(f"oracle0:{c['direction']}:{c['d']}")
        if c.get('oracle_semantic_count_sigma0')!=e1: errs.append(f"oracle1:{c['direction']}:{c['d']}")
    return {'pass':not errs,'errors':errs,'cells':len(cells)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out'); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text())
    out=audit_construction(r) if r.get('phase')=='construction' else audit_characterization(r)
    s=json.dumps(out,indent=2,sort_keys=True)+'\n'; print(s,end='')
    if a.out: Path(a.out).write_text(s)
    raise SystemExit(0 if out['pass'] else 5)
if __name__=='__main__': main()
