from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

TASK='VISUAL-INVALIDATION-ROI-TRANSLATION-ENVELOPE-A2-20260918-002'
ROI=48
TARGET=12
BG=64
TARGET_BASE=128
TARGET_CHANGED=144
SIGMA=2.0
PIXEL_DELTA=12
COUNT_THRESHOLD=100
TARGET_X=18
TARGET_Y=18
DIRECTIONS={'horizontal':(1,0),'vertical':(0,1),'diagonal':(1,1)}
CHAR_SEED=149520260918002
TRIALS=1000
CONSTRUCTION_SEED=1522001


def clip_rect(x,y,w=TARGET,h=TARGET):
    x0=max(0,x); y0=max(0,y); x1=min(ROI,x+w); y1=min(ROI,y+h)
    return x0,y0,x1,y1


def template(direction:str,d:int,semantic_change:bool):
    src=np.full((ROI,ROI),BG,dtype=np.float32)
    cur=np.full((ROI,ROI),BG,dtype=np.float32)
    src[TARGET_Y:TARGET_Y+TARGET,TARGET_X:TARGET_X+TARGET]=TARGET_BASE
    ux,uy=DIRECTIONS[direction]
    x0,y0,x1,y1=clip_rect(TARGET_X+ux*d,TARGET_Y+uy*d)
    if x1>x0 and y1>y0:
        cur[y0:y1,x0:x1]=TARGET_CHANGED if semantic_change else TARGET_BASE
    return src,cur


def detector_counts_batch(src_base,cur_base,noise_src,noise_cur):
    src=np.clip(np.rint(src_base[None,:,:]+noise_src),0,255).astype(np.uint8)
    cur=np.clip(np.rint(cur_base[None,:,:]+noise_cur),0,255).astype(np.uint8)
    diff=np.abs(src.astype(np.int16)-cur.astype(np.int16))
    return np.count_nonzero(diff>=PIXEL_DELTA,axis=(1,2)).astype(np.int32)


def detector_count_scalar(src_base,cur_base,noise_src,noise_cur):
    src=np.clip(np.rint(src_base+noise_src),0,255).astype(np.uint8)
    cur=np.clip(np.rint(cur_base+noise_cur),0,255).astype(np.uint8)
    return int(np.count_nonzero(np.abs(src.astype(np.int16)-cur.astype(np.int16))>=PIXEL_DELTA))


def oracle_count(direction:str,d:int,semantic_change:bool)->int:
    ux,uy=DIRECTIONS[direction]
    ax0,ay0,ax1,ay1=TARGET_X,TARGET_Y,TARGET_X+TARGET,TARGET_Y+TARGET
    bx0,by0,bx1,by1=clip_rect(TARGET_X+ux*d,TARGET_Y+uy*d)
    aa=(ax1-ax0)*(ay1-ay0)
    bb=max(0,bx1-bx0)*max(0,by1-by0)
    ix=max(0,min(ax1,bx1)-max(ax0,bx0))
    iy=max(0,min(ay1,by1)-max(ay0,by0))
    inter=ix*iy
    return aa+bb-inter if semantic_change else aa+bb-2*inter


def construction(out:Path):
    rng=np.random.default_rng(CONSTRUCTION_SEED)
    geom=[]; geom_mismatch=[]
    zeros=np.zeros((ROI,ROI),dtype=np.float32)
    for direction in DIRECTIONS:
        for d in range(25):
            for semantic in (False,True):
                sb,cb=template(direction,d,semantic)
                count=detector_count_scalar(sb,cb,zeros,zeros)
                expected=oracle_count(direction,d,semantic)
                row={'direction':direction,'d':d,'semantic_change':semantic,'count':count,'oracle_count':expected}
                geom.append(row)
                if count!=expected: geom_mismatch.append(row)

    selected=[('horizontal',4),('horizontal',5),('vertical',4),('vertical',5),('diagonal',2),('diagonal',3),
              ('horizontal',1),('vertical',12),('diagonal',8),('horizontal',24),('vertical',24),('diagonal',24)]
    scalar_batch_mismatch=[]; checks=[]
    for direction,d in selected:
        for semantic in (False,True):
            sb,cb=template(direction,d,semantic)
            ns=rng.normal(0.0,SIGMA,size=(64,ROI,ROI))
            nc=rng.normal(0.0,SIGMA,size=(64,ROI,ROI))
            batch=detector_counts_batch(sb,cb,ns,nc)
            scalar=np.array([detector_count_scalar(sb,cb,ns[i],nc[i]) for i in range(64)],dtype=np.int32)
            eq=bool(np.array_equal(batch,scalar))
            checks.append({'direction':direction,'d':d,'semantic_change':semantic,'pairs':64,'equal':eq,
                           'count_min':int(batch.min()),'count_max':int(batch.max())})
            if not eq:
                scalar_batch_mismatch.append({'direction':direction,'d':d,'semantic_change':semantic,
                                              'indices':np.flatnonzero(batch!=scalar).tolist()})

    boundary=[]
    for direction,d in [('horizontal',4),('horizontal',5),('vertical',4),('vertical',5),('diagonal',2),('diagonal',3)]:
        ns=rng.normal(0.0,SIGMA,size=(250,ROI,ROI)); nc=rng.normal(0.0,SIGMA,size=(250,ROI,ROI))
        sb,cb=template(direction,d,False); a=detector_counts_batch(sb,cb,ns,nc)
        ns2=rng.normal(0.0,SIGMA,size=(250,ROI,ROI)); nc2=rng.normal(0.0,SIGMA,size=(250,ROI,ROI))
        sb2,cb2=template(direction,d,True); b=detector_counts_batch(sb2,cb2,ns2,nc2)
        boundary.append({'direction':direction,'d':d,'translation_invalidation_rate':float(np.mean(a>=COUNT_THRESHOLD)),
                         'semantic_detect_rate':float(np.mean(b>=COUNT_THRESHOLD)),
                         'translation_count_minmax':[int(a.min()),int(a.max())],
                         'semantic_count_minmax':[int(b.min()),int(b.max())]})

    pass_shape=(not geom_mismatch and not scalar_batch_mismatch and
        all(x['translation_invalidation_rate']<=0.01 for x in boundary if (x['direction']!='diagonal' and x['d']==4) or (x['direction']=='diagonal' and x['d']==2)) and
        all(x['translation_invalidation_rate']>=0.99 for x in boundary if (x['direction']!='diagonal' and x['d']==5) or (x['direction']=='diagonal' and x['d']==3)) and
        all(x['semantic_detect_rate']>=0.99 for x in boundary))
    result={'task':TASK,'phase':'construction','construction_seed':CONSTRUCTION_SEED,'characterization_seed_used':False,
            'formal_invocations':0,'reruns':0,'replacements':0,'tuning':0,
            'geometry_rows':geom,'geometry_mismatches':geom_mismatch,
            'scalar_batch_checks':checks,'scalar_batch_mismatches':scalar_batch_mismatch,
            'boundary':boundary,'decision':'PASS_CONSTRUCTION_ELIGIBLE' if pass_shape else 'STOP_CONSTRUCTION_INTEGRITY'}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':result['decision'],'geometry_mismatches':len(geom_mismatch),'scalar_batch_mismatches':len(scalar_batch_mismatch)}))


def characterization(out:Path):
    rng=np.random.default_rng(CHAR_SEED)
    cells=[]
    for direction in DIRECTIONS:
        for d in range(25):
            row={'direction':direction,'d':d,'trials_per_class':TRIALS}
            for semantic,label in ((False,'translation'),(True,'semantic')):
                sb,cb=template(direction,d,semantic)
                ns=rng.normal(0.0,SIGMA,size=(TRIALS,ROI,ROI))
                nc=rng.normal(0.0,SIGMA,size=(TRIALS,ROI,ROI))
                counts=detector_counts_batch(sb,cb,ns,nc)
                flags=counts>=COUNT_THRESHOLD
                row['oracle_'+label+'_count_sigma0']=oracle_count(direction,d,semantic)
                row[label+'_count']={'min':int(counts.min()),'median':float(np.median(counts)),'p05':float(np.percentile(counts,5)),
                                      'p95':float(np.percentile(counts,95)),'max':int(counts.max())}
                if semantic: row['fnr']=float(1.0-np.mean(flags))
                else: row['fpr']=float(np.mean(flags))
            cells.append(row)

    bounds={}
    for direction in DIRECTIONS:
        xs=[c for c in cells if c['direction']==direction]
        safe=[c['d'] for c in xs if c['d']>0 and c['fpr']<=0.01 and c['fnr']<=0.01]
        fail=[c['d'] for c in xs if c['d']>0 and c['fpr']>0.01]
        hard=[c['d'] for c in xs if c['d']>0 and c['fpr']>=0.99]
        bounds[direction]={'last_d_fpr_le_1pct':max(safe) if safe else None,
                           'first_d_fpr_gt_1pct':min(fail) if fail else None,
                           'first_d_fpr_ge_99pct':min(hard) if hard else None}
    d0=max(c['fnr'] for c in cells if c['d']==0)
    if d0>0.01:
        decision='FAIL_DETECTOR_SENSITIVITY'
    elif any(next(c for c in cells if c['direction']==k and c['d']==1)['fpr']>0.01 for k in DIRECTIONS):
        decision='REJECT_FIXED_ROI_TRANSLATION_TOLERANCE'
    elif all(bounds[k]['last_d_fpr_le_1pct'] is not None and bounds[k]['first_d_fpr_ge_99pct'] is not None for k in DIRECTIONS):
        decision='RETAIN_FIXED_ROI_TRANSLATION_ENVELOPE_SCOPED'
    else:
        decision='FAIL_INTEGRITY'
    result={'task':TASK,'phase':'characterization','seed':CHAR_SEED,'trials_per_class_per_cell':TRIALS,
            'formal_invocations':0,'characterization_invocations':1,'reruns':0,'replacements':0,'tuning':0,
            'constants':{'roi':ROI,'target':TARGET,'background':BG,'target_base':TARGET_BASE,'target_changed':TARGET_CHANGED,
                         'sigma':SIGMA,'pixel_delta':PIXEL_DELTA,'count_threshold':COUNT_THRESHOLD},
            'decision':decision,'bounds':bounds,'d0_max_fnr':d0,'cells':cells,
            'limits':['synthetic independent Gaussian jitter','translation explicitly permitted by policy','direct ROI distribution; fresh RNG stream','no X11/capture/task efficacy claim']}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'bounds':bounds,'d0_max_fnr':d0},sort_keys=True))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--phase',choices=['construction','characterization'],required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); out=Path(a.out)
    if a.phase=='construction': construction(out)
    else: characterization(out)

if __name__=='__main__': main()
