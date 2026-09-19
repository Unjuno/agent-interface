from __future__ import annotations
import argparse, json, math, platform, hashlib
from pathlib import Path
import numpy as np

TASK='VISUAL-INVALIDATION-ROI-TRANSLATION-ENVELOPE-20260918-001'
CANVAS=256
ROI=48
TARGET=12
BG=64
TARGET_BASE=128
TARGET_CHANGED=144
SIGMA=2.0
PIXEL_DELTA=12
COUNT_THRESHOLD=100
ROI_X=104
ROI_Y=104
TARGET_X=ROI_X+18
TARGET_Y=ROI_Y+18
DIRECTIONS={'horizontal':(1,0),'vertical':(0,1),'diagonal':(1,1)}
FORMAL_SEED=149420260918001


def rect_pixels(x:int,y:int,w:int,h:int):
    return {(xx,yy) for yy in range(y,y+h) for xx in range(x,x+w)}


def in_roi(p):
    x,y=p
    return ROI_X <= x < ROI_X+ROI and ROI_Y <= y < ROI_Y+ROI


def oracle_count(direction:str,d:int,semantic_change:bool)->int:
    dxu,dyu=DIRECTIONS[direction]
    a={p for p in rect_pixels(TARGET_X,TARGET_Y,TARGET,TARGET) if in_roi(p)}
    b={p for p in rect_pixels(TARGET_X+dxu*d,TARGET_Y+dyu*d,TARGET,TARGET) if in_roi(p)}
    if semantic_change:
        # overlap pixels change by +16 and therefore count at sigma=0;
        # non-overlap target/background pixels also exceed the threshold.
        return len(a|b)
    return len(a^b)


def render(direction:str,d:int,semantic_change:bool,rng:np.random.Generator,sigma:float=SIGMA):
    src=np.full((CANVAS,CANVAS),BG,dtype=np.float32)
    cur=np.full((CANVAS,CANVAS),BG,dtype=np.float32)
    src[TARGET_Y:TARGET_Y+TARGET,TARGET_X:TARGET_X+TARGET]=TARGET_BASE
    dxu,dyu=DIRECTIONS[direction]
    x=TARGET_X+dxu*d; y=TARGET_Y+dyu*d
    val=TARGET_CHANGED if semantic_change else TARGET_BASE
    cur[y:y+TARGET,x:x+TARGET]=val
    if sigma:
        src += rng.normal(0.0,sigma,src.shape)
        cur += rng.normal(0.0,sigma,cur.shape)
    src=np.clip(np.rint(src),0,255).astype(np.uint8)
    cur=np.clip(np.rint(cur),0,255).astype(np.uint8)
    return src,cur


def detector(src,cur):
    a=src[ROI_Y:ROI_Y+ROI,ROI_X:ROI_X+ROI].astype(np.int16)
    b=cur[ROI_Y:ROI_Y+ROI,ROI_X:ROI_X+ROI].astype(np.int16)
    count=int(np.count_nonzero(np.abs(a-b)>=PIXEL_DELTA))
    return count, count>=COUNT_THRESHOLD


def construction(out:Path):
    mismatches=[]; rows=[]
    rng=np.random.default_rng(1495001)
    # Exact sigma=0 oracle check for all frozen cells.
    for direction in DIRECTIONS:
        for d in range(25):
            for semantic in (False,True):
                src,cur=render(direction,d,semantic,rng,sigma=0.0)
                count,flag=detector(src,cur)
                expected=oracle_count(direction,d,semantic)
                row={'direction':direction,'d':d,'semantic_change':semantic,'count':count,'oracle_count':expected,'invalidate':flag}
                rows.append(row)
                if count!=expected:
                    mismatches.append(row)
    # Boundary challenges under sigma=2, excluded from fixed-seed characterization.
    boundary=[('horizontal',4),('horizontal',5),('vertical',4),('vertical',5),('diagonal',2),('diagonal',3)]
    challenge=[]
    for direction,d in boundary:
        flags=[]; changed_flags=[]
        counts=[]; changed_counts=[]
        for _ in range(250):
            s,c=render(direction,d,False,rng)
            n,f=detector(s,c); counts.append(n); flags.append(f)
            s,c=render(direction,d,True,rng)
            n,f=detector(s,c); changed_counts.append(n); changed_flags.append(f)
        challenge.append({'direction':direction,'d':d,
            'translation_only_invalidate_rate':sum(flags)/len(flags),
            'semantic_detect_rate':sum(changed_flags)/len(changed_flags),
            'translation_count_minmax':[min(counts),max(counts)],
            'semantic_count_minmax':[min(changed_counts),max(changed_counts)]})
    pass_shape=(not mismatches and
        all(x['translation_only_invalidate_rate']<=0.01 for x in challenge if (x['direction']!='diagonal' and x['d']==4) or (x['direction']=='diagonal' and x['d']==2)) and
        all(x['translation_only_invalidate_rate']>=0.99 for x in challenge if (x['direction']!='diagonal' and x['d']==5) or (x['direction']=='diagonal' and x['d']==3)) and
        all(x['semantic_detect_rate']>=0.99 for x in challenge))
    result={'task':TASK,'phase':'construction','formal_invocations':0,'reruns':0,'mismatches':mismatches,
            'noise_free_rows':rows,'boundary_challenge':challenge,
            'decision':'PASS_CONSTRUCTION_ELIGIBLE' if pass_shape else 'STOP_CONSTRUCTION_UNEXPECTED_BOUNDARY'}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result


def characterization(out:Path, seed:int=FORMAL_SEED, trials:int=1000):
    rng=np.random.default_rng(seed)
    cells=[]
    for direction in DIRECTIONS:
        for d in range(25):
            no_flags=[]; yes_flags=[]; no_counts=[]; yes_counts=[]
            for _ in range(trials):
                s,c=render(direction,d,False,rng)
                n,f=detector(s,c); no_counts.append(n); no_flags.append(f)
                s,c=render(direction,d,True,rng)
                n,f=detector(s,c); yes_counts.append(n); yes_flags.append(f)
            cells.append({'direction':direction,'d':d,'trials_per_class':trials,
                'oracle_translation_only_count_sigma0':oracle_count(direction,d,False),
                'oracle_semantic_count_sigma0':oracle_count(direction,d,True),
                'fpr':sum(no_flags)/trials,'fnr':1.0-sum(yes_flags)/trials,
                'translation_count':{'min':min(no_counts),'median':float(np.median(no_counts)),'p95':float(np.percentile(no_counts,95)),'max':max(no_counts)},
                'semantic_count':{'min':min(yes_counts),'median':float(np.median(yes_counts)),'p05':float(np.percentile(yes_counts,5)),'max':max(yes_counts)}})
    bounds={}
    for direction in DIRECTIONS:
        xs=[c for c in cells if c['direction']==direction]
        safe=[c['d'] for c in xs if c['d']>0 and c['fpr']<=0.01 and c['fnr']<=0.01]
        fail=[c['d'] for c in xs if c['d']>0 and c['fpr']>0.01]
        hard=[c['d'] for c in xs if c['d']>0 and c['fpr']>=0.99]
        bounds[direction]={'last_d_fpr_le_1pct':max(safe) if safe else None,
                           'first_d_fpr_gt_1pct':min(fail) if fail else None,
                           'first_d_fpr_ge_99pct':min(hard) if hard else None}
    d0=[c for c in cells if c['d']==0]
    sensitivity=max(c['fnr'] for c in d0)
    conditions=(sensitivity<=0.01 and all(bounds[k]['last_d_fpr_le_1pct'] is not None for k in bounds)
                and all(bounds[k]['first_d_fpr_ge_99pct'] is not None for k in bounds))
    if sensitivity>0.01: decision='FAIL_DETECTOR_SENSITIVITY'
    elif any(next(c for c in cells if c['direction']==k and c['d']==1)['fpr']>0.01 for k in DIRECTIONS): decision='REJECT_FIXED_ROI_TRANSLATION_TOLERANCE'
    elif conditions: decision='RETAIN_FIXED_ROI_TRANSLATION_ENVELOPE_SCOPED'
    else: decision='FAIL_INTEGRITY'
    result={'task':TASK,'phase':'characterization','seed':seed,'trials_per_class_per_cell':trials,
            'formal_invocations':0,'reruns':0,'replacements':0,'tuning':0,
            'constants':{'canvas':CANVAS,'roi':ROI,'target':TARGET,'background':BG,'target_base':TARGET_BASE,'target_changed':TARGET_CHANGED,'sigma':SIGMA,'pixel_delta':PIXEL_DELTA,'count_threshold':COUNT_THRESHOLD},
            'decision':decision,'bounds':bounds,'d0_max_fnr':sensitivity,'cells':cells,
            'limits':['synthetic independent Gaussian jitter','translation explicitly permitted by policy','no X11/capture/task efficacy claim']}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--phase',choices=['construction','characterization'],required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); out=Path(a.out)
    if a.phase=='construction': r=construction(out)
    else: r=characterization(out)
    print(json.dumps({'phase':r['phase'],'decision':r['decision']},sort_keys=True))

if __name__=='__main__': main()
