"""Independent raw-image auditor. Does not import experiment or use NumPy."""
from __future__ import annotations
import argparse, copy, hashlib, io, json, math, random, statistics
from pathlib import Path
from PIL import Image, ImageChops
P=('GLOBAL_AHASH_ONLY','AHASH_EXACT_FALLBACK','EXACT_ONLY')
S=('unchanged','noise','text','selection','critical','large')

def require(condition, message):
    if not condition: raise ValueError(message)

def integer(x, minimum=0):
    return type(x) is int and x>=minimum

def digest(b): return hashlib.sha256(b).hexdigest()

def independent_hash(raw):
    sums=[]
    for by in range(8):
        for bx in range(8):
            cell=0
            for y in range(by*30,(by+1)*30):
                offset=(y*320+bx*40)*3
                cell+=sum(raw[offset:offset+120])
            sums.append(cell)
    total=sum(sums);number=0
    for cell in sums: number=(number<<1)|int(cell*64>=total)
    return f'{number:016x}'

def ci(values,seed):
    rng=random.Random(seed);n=len(values);means=[]
    for _ in range(1000):
        means.append(sum(values[rng.randrange(n)] for j in range(n))/n)
    means.sort()
    return [means[24],means[974]]

def verify(root: Path, rows=None):
    plan=json.loads((root.parent/'PLAN.json').read_text())
    sources=json.loads((root/'source.json').read_text())
    for name,wanted in sources.items():
        require(digest((root.parent/name).read_bytes())==wanted,'source '+name)
    invocation=json.loads((root/'invocation.json').read_text())
    formal=invocation['formal']
    require(type(formal) is bool,'formal type')
    require(type(invocation['invocations']) is int and invocation['invocations']==1,'invocations')
    require(type(invocation['retries']) is int and invocation['retries']==0,'retries')
    exit_record=json.loads((root/'exit.json').read_text())
    require(type(exit_record['returncode']) is int and exit_record['returncode']==0,'process exit')
    if formal:
        require(sources==json.loads((root.parent/'SOURCE_MANIFEST.json').read_text()),'frozen sources')
    expected=[];rng=random.Random(256120260922)
    for f in (range(10) if formal else [0]):
        for v in (range(5) if formal else [99]):
            for s in S:
                order=list(P);rng.shuffle(order)
                expected.append((f,v,s,order))
    if rows is None:
        rows=[json.loads(line) for line in (root/'rows.jsonl').read_text().splitlines()]
    require(len(rows)==len(expected),'row cardinality')
    require(len({r['id'] for r in rows})==len(rows),'duplicate case')
    network=json.loads((root/'network.json').read_text())
    require(type(network['count']) is int and network=={'blocked_requests':[],'count':0},'unexpected network')
    env=json.loads((root/'environment.json').read_text())
    require(env['rgb_bytes_per_frame']==230400 and env['model_calls']==0 and env['os_task_input_calls']==0,'environment scope')
    counts={s:{'pairs':0,'task_relevant':0,**{p:{'forward':0,'fallback':0,'false_task_suppression':0,'false_forward_unchanged':0} for p in P}} for s in S}
    timings={p:[] for p in P};gaps=[];family_gaps={f:[] for f,_,_,_ in expected}
    seen_png={};areas={s:[] for s in S}
    for index,(r,(f,v,s,order)) in enumerate(zip(rows,expected)):
        require(r['id']==f'f{f:02d}-v{v:02d}-{s}','case order')
        require(type(r['family']) is int and r['family']==f and type(r['variant']) is int and r['variant']==v,'case integer identity')
        require(r['stratum']==s and r['policy_order']==order,'stratum/order')
        relevant=s in ('text','selection','critical','large')
        require(type(r['must_forward']) is bool and r['must_forward']==relevant,'label')
        require(r['semantic_importance']==('task' if relevant else 'benign'),'semantic label')
        require(integer(r['changed_pixels']) and type(r['exact_same']) is bool,'pixel types')
        require(set(r['decisions'])==set(P),'policy denominator')
        for p,d in r['decisions'].items():
            require(type(d['forward']) is bool and type(d['exact_fallback']) is bool,'decision bool')
            require(integer(d['batch_elapsed_ns'],1) and type(d['repeats']) is int and d['repeats']==plan['timing_repeats'],'timing integer')
        require(len(r['images'])==2 and len(r['receipts'])==2 and len(r['hashes'])==2,'pair denominator')
        decoded=[];raws=[]
        for side,img in enumerate(r['images']):
            h=img['png_sha256'];require(type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h),'image identity')
            data=(root/'frames'/(h+'.png')).read_bytes()
            require(digest(data)==h and type(img['png_bytes']) is int and len(data)==img['png_bytes'],'PNG binding')
            im=Image.open(io.BytesIO(data)).convert('RGB');require(im.size==(320,240),'raster dimensions')
            b=im.tobytes();require(digest(b)==img['rgb_sha256'],'RGB binding')
            ah=independent_hash(b);require(ah==r['hashes'][side],'independent block hash')
            decoded.append(im);raws.append(b);seen_png[h]=len(data)
            receipt=r['receipts'][side]
            state={'counter':v+10,'selection':0,'alert':False,'panel':'closed','noise':0}
            region=None
            if side:
                if s=='noise':state['noise']=1;region=[278+(v%5),225,1,1]
                if s=='text':state['counter']+=1;region=[214,221,103,19]
                if s=='selection':state['selection']=1;region=[60+f*4,174,2,27]
                if s=='critical':state['alert']=True;region=[291,9,4,4]
                if s=='large':state['panel']='open';region=[85+(v%5)*2,68,170,106]
            expected_receipt={'family':f,'variant':v,'stratum':s,'after':bool(side),'state':state,'region':region}
            require(json.dumps(receipt,sort_keys=True)==json.dumps(expected_receipt,sort_keys=True),'fixture state receipt')
        diff=ImageChops.difference(*decoded)
        channels=diff.split();mask=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
        changed=sum(mask.histogram()[1:]);bbox=mask.getbbox()
        bbox=None if bbox is None else [bbox[0],bbox[1],bbox[2]-bbox[0],bbox[3]-bbox[1]]
        same=raws[0]==raws[1];hashsame=r['hashes'][0]==r['hashes'][1]
        require(changed==r['changed_pixels'] and bbox==r['changed_bbox'] and same==r['exact_same'],'pixel oracle')
        require(same==(s=='unchanged'),'expected changed stratum')
        if bbox is not None:
            x,y,w,h=r['receipts'][1]['region'];bx,by,bw,bh=bbox
            require(x<=bx and y<=by and bx+bw<=x+w and by+bh<=y+h,'declared region containment')
        expected_decisions={P[0]:(not hashsame,False),P[1]:(not same,hashsame),P[2]:(not same,False)}
        counts[s]['pairs']+=1;counts[s]['task_relevant']+=int(relevant);areas[s].append(changed)
        for p,d in r['decisions'].items():
            require((d['forward'],d['exact_fallback'])==expected_decisions[p],'policy result')
            c=counts[s][p];c['forward']+=int(d['forward']);c['fallback']+=int(d['exact_fallback'])
            c['false_task_suppression']+=int(relevant and not d['forward'])
            c['false_forward_unchanged']+=int(same and d['forward'])
            timings[p].append(d['batch_elapsed_ns']/d['repeats'])
        gap=timings[P[1]][-1]-timings[P[2]][-1];gaps.append(gap);family_gaps[f].append(gap)
    require(set(p.name for p in (root/'frames').iterdir())==set(h+'.png' for h in seen_png),'frame denominator')
    families=[statistics.mean(g) for g in family_gaps.values()]
    paired_ci=ci(gaps,256122);cluster_ci=ci(families,256123)
    faults={p:sum(counts[s][p]['false_task_suppression'] for s in S) for p in P}
    if faults[P[1]] or faults[P[2]]:status='FAIL_UNSAFE_FALLBACK'
    elif not faults[P[0]]:status='HOLD_NO_NATURAL_COLLISION'
    elif not (paired_ci[1]<0 and cluster_ci[1]<0):status='HOLD_NO_RUNTIME_SAVING'
    else:status='PASS_FALLBACK_SAFETY_AND_MEASURED_VALUE_SCOPED'
    result={'status':status,'audit':'PASS_RAW_RECONSTRUCTION','rows':len(rows),'formal':formal,
            'counts':counts,'task_false_suppression':faults,'unique_pngs':len(seen_png),'png_bytes':sum(seen_png.values()),
            'timing_ns_per_call':{p:{'mean':statistics.mean(t),'median':statistics.median(t),'p95_batch_mean':sorted(t)[math.ceil(.95*len(t))-1]} for p,t in timings.items()},
            'paired_mean_gap_ns':statistics.mean(gaps),'paired_mean_gap_95pct_ci_ns':paired_ci,
            'family_cluster_mean_gap_95pct_ci_ns':cluster_ci,
            'family_mean_gap_ns':{str(f):statistics.mean(g) for f,g in family_gaps.items()},
            'changed_pixels_by_stratum':{s:{'min':min(a),'max':max(a)} for s,a in areas.items()},
            'memory':json.loads((root/'memory.json').read_text())}
    return result

def corruption_controls(root):
    original=[json.loads(line) for line in (root/'rows.jsonl').read_text().splitlines()]
    cases={}
    for name in ('missing_row','duplicate_row','changed_hash','boolean_time','wrong_label','wrong_decision','wrong_receipt'):
        rows=copy.deepcopy(original)
        if name=='missing_row':rows.pop()
        elif name=='duplicate_row':rows[1]=copy.deepcopy(rows[0])
        elif name=='changed_hash':rows[0]['hashes'][0]='0'*16
        elif name=='boolean_time':rows[0]['decisions'][P[0]]['batch_elapsed_ns']=True
        elif name=='wrong_label':rows[0]['must_forward']=True
        elif name=='wrong_decision':rows[0]['decisions'][P[1]]['forward']=True
        elif name=='wrong_receipt':rows[0]['receipts'][1]['state']['alert']=True
        try:verify(root,rows)
        except ValueError as e:cases[name]={'rejected':True,'reason':str(e)}
        else:raise AssertionError('accepted corrupted '+name)
    return cases

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--controls',action='store_true')
    a=ap.parse_args();result=verify(a.root)
    if a.controls:result['corruption_controls']=corruption_controls(a.root)
    print(json.dumps(result,sort_keys=True,indent=2,allow_nan=False))
