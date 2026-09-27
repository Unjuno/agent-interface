from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path
from candidate import Frame, global_ahash_only, ahash_plus_exact_fallback
from oracle import exact_semantic_oracle

TASK='OBSERVATION-GATING-TINY-CHANGE-AHASH-STRESS-20260918-001'
SEED=155920260918001
COUNTS=[
 ('UNCHANGED',30000),('SINGLE_PIXEL',30000),('STATUS_DOT_2X2',25000),
 ('CURSOR_1X3',20000),('GLYPH_STROKE_1X4',20000),('LOCAL_BLOCK_4X4',15000),('HASH_FLIP',10000)
]
TOTAL=sum(n for _,n in COUNTS)

def base_frame(i:int)->Frame:
    vals=[]; shift=i&1
    for b in range(64):
        jitter=((i*17+b*13)%11)-5
        high=((b+shift)&1)==1
        vals.append((176 if high else 80)+jitter)
    return Frame(tuple(vals),())

def local_positions(family:str)->list[int]:
    return {
        'SINGLE_PIXEL':[0],
        'STATUS_DOT_2X2':[0,1,8,9],
        'CURSOR_1X3':[0,8,16],
        'GLYPH_STROKE_1X4':[0,1,2,3],
        'LOCAL_BLOCK_4X4':[0,1,2,3,8,9,10,11,16,17,18,19,24,25,26,27],
        'HASH_FLIP':list(range(64)),
    }[family]

def mutate(base:Frame,i:int,family:str)->Frame:
    if family=='UNCHANGED':
        return base
    block=(i*7+3)%64
    basev=base.blocks[block]
    target=255 if basev<128 else 0
    return Frame(base.blocks,tuple((block*64+p,target) for p in local_positions(family)))

def schedule()->list[str]:
    arr=[]
    for fam,n in COUNTS: arr.extend([fam]*n)
    random.Random(SEED).shuffle(arr)
    return arr

def eval_pair(i:int,family:str)->dict:
    a=base_frame(i); b=mutate(a,i,family)
    oracle=exact_semantic_oracle(family,a.canonical(),b.canonical())
    approx=global_ahash_only(a,b)
    fallback=ahash_plus_exact_fallback(a,b)
    return {'family':family,'scope':f's{i%4}','oracle':oracle,'approx':approx,'fallback':fallback}

def construction()->dict:
    rows=[]
    for j,(fam,_) in enumerate(COUNTS):
        for k in range(3):
            rows.append(eval_pair(j*17+k,fam))
    malformed=[]
    tests=[
      ('bad_blocks', lambda: Frame(tuple([1]*63),())),
      ('bad_block_value', lambda: Frame(tuple([1]*63+[999]),())),
      ('bad_pixel_index', lambda: Frame(tuple([100]*64),((4096,1),))),
      ('bad_pixel_value', lambda: Frame(tuple([100]*64),((0,-1),))),
      ('duplicate_override', lambda: Frame(tuple([100]*64),((0,1),(0,2)))),
    ]
    for name,fn in tests:
        try: fn(); malformed.append({'name':name,'rejected':False})
        except ValueError: malformed.append({'name':name,'rejected':True})
    return {'task':TASK,'phase':'construction','formal_invocations':0,'reruns':0,'replacements':0,'tuning':0,'rows':rows,'malformed':malformed}

def formal(source_sha256:dict)->dict:
    fam_metrics={fam:{'pairs':0,'must_forward':0,'hash_equal':0,'hash_diff':0,'ahash_false_suppress':0,'ahash_false_forward':0,
                      'fallback_calls':0,'fallback_false_suppress':0,'fallback_suppressed_exact':0,'fallback_forwarded_change':0}
                 for fam,_ in COUNTS}
    digest=hashlib.sha256(); samples=[]; corpus_errors=0
    for i,fam in enumerate(schedule()):
        row=eval_pair(i,fam); m=fam_metrics[fam]; m['pairs']+=1
        oracle=row['oracle']; approx=row['approx']; fb=row['fallback']
        m['must_forward']+=int(oracle['must_forward'])
        m['hash_equal']+=int(approx['hash_equal']); m['hash_diff']+=int(not approx['hash_equal'])
        m['ahash_false_suppress']+=int(oracle['must_forward'] and approx['suppress'])
        m['ahash_false_forward']+=int((not oracle['must_forward']) and (not approx['suppress']))
        m['fallback_calls']+=int(fb['exact_fallback'])
        m['fallback_false_suppress']+=int(oracle['must_forward'] and fb['suppress'])
        m['fallback_suppressed_exact']+=int((not oracle['must_forward']) and fb['suppress'])
        m['fallback_forwarded_change']+=int(oracle['must_forward'] and (not fb['suppress']))
        if fam=='UNCHANGED' and not oracle['exact_equal']: corpus_errors+=1
        if fam!='UNCHANGED' and oracle['exact_equal']: corpus_errors+=1
        compact={'i':i,'family':fam,'oracle':oracle,'approx':approx,'fallback':fb}
        digest.update(json.dumps(compact,sort_keys=True,separators=(',',':')).encode())
        if len(samples)<28: samples.append(compact)
    totals={k:sum(m[k] for m in fam_metrics.values()) for k in next(iter(fam_metrics.values()))}
    return {'task':TASK,'phase':'formal','seed':SEED,'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
            'source_sha256':source_sha256,'corpus_errors':corpus_errors,'family_metrics':fam_metrics,'totals':totals,
            'ledger_sha256':digest.hexdigest(),'samples':samples}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--phase',choices=['construction','formal'],required=True); ap.add_argument('--out',required=True); ap.add_argument('--source-manifest')
    a=ap.parse_args()
    if a.phase=='construction': out=construction()
    else:
        if not a.source_manifest: raise SystemExit('--source-manifest required')
        out=formal(json.loads(Path(a.source_manifest).read_text())['sha256'])
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'phase':a.phase,'rows':len(out.get('rows',[])),'totals':out.get('totals')},sort_keys=True))
if __name__=='__main__': main()
