"""Measure one immutable-artifact condition; never run an input backend."""
import hashlib, json, os, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'vendor'))
from runtime.cli_v1 import review, snapshot_review
from fixture import create, canon
FUNCS={'baseline':review.review_bytes,'candidate':snapshot_review.review_bytes}


def sha(data): return hashlib.sha256(data).hexdigest()


def check_sources():
    freeze=ROOT/'FREEZE.json'
    if freeze.exists():
        for path,h in json.loads(freeze.read_text())['files'].items():
            if sha((ROOT/path).read_bytes())!=h: raise ValueError('SOURCE_CHANGED:'+path)
    for ent in json.loads((ROOT/'VENDOR.json').read_text())['modules']:
        b=(ROOT/'vendor'/ent['path']).read_bytes()
        if sha(b)!=ent['sha256']: raise ValueError('VENDOR_CHANGED')


def measured(fn, raw, root):
    w0=time.perf_counter_ns(); c0=time.process_time_ns()
    out=canon(fn(raw,root,compact=False))
    c1=time.process_time_ns(); w1=time.perf_counter_ns()
    return out,{'wall_start_ns':w0,'wall_end_ns':w1,'cpu_start_ns':c0,'cpu_end_ns':c1}


def counted(fn, raw, root):
    original=Path.read_bytes; reads=[]
    def read(path):
        data=original(path)
        reads.append({'path':str(path),'bytes':len(data),'sha256':sha(data)})
        return data
    Path.read_bytes=read
    try: out=canon(fn(raw,root,compact=False))
    finally: Path.read_bytes=original
    return out,reads


def run(out, config, pairs, warmup):
    check_sources()
    plan=json.loads((ROOT/'PLAN.json').read_text())
    os.sched_setaffinity(0,{plan['affinity']})
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    inputs=out/'inputs'; create(inputs,config['width'],config['height'],config['level'])
    raw=(inputs/'report.json').read_bytes()
    before={p.name:sha(p.read_bytes()) for p in inputs.iterdir()}
    rows=[];first={}
    for stage,n in [('warmup',warmup),('measured',pairs)]:
        for i in range(n):
            order=['baseline','candidate'] if i%2==0 else ['candidate','baseline']
            for policy in order:
                data,clocks=measured(FUNCS[policy],raw,inputs)
                h=sha(data)
                if policy not in first:
                    first[policy]=h;(out/(policy+'.json')).write_bytes(data)
                elif h!=first[policy]: raise ValueError('NONDETERMINISTIC_OUTPUT')
                row={'stage':stage,'pair':i,'policy':policy,'sha256':h,'bytes':len(data),**clocks}
                rows.append(row)
                with (out/'samples.jsonl').open('ab') as f: f.write(canon(row)+b'\n')
    accounting={}
    for policy,fn in FUNCS.items():
        data,reads=counted(fn,raw,inputs)
        if sha(data)!=first[policy]: raise ValueError('ACCOUNTING_OUTPUT_CHANGED')
        accounting[policy]={'reads':reads,'output_sha256':sha(data)}
    after={p.name:sha(p.read_bytes()) for p in inputs.iterdir()}
    record={'condition':config,'pid':os.getpid(),'argv':sys.argv,'affinity':sorted(os.sched_getaffinity(0)),
            'pairs':pairs,'warmup_pairs':warmup,'before':before,'after':after,'accounting':accounting,
            'imports':{k:str(v.__file__) for k,v in sys.modules.items() if k.startswith('runtime.') and getattr(v,'__file__',None)},
            'backend_invoked':False,'model_invoked':False}
    (out/'RECORD.json').write_bytes(canon(record))
    check_sources()
    print(json.dumps({'condition':config['id'],'samples':len(rows),'pid':os.getpid()}),flush=True)


def controls(out):
    check_sources()
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    allrows=[]
    for condition in json.loads((ROOT/'PLAN.json').read_text())['control_conditions']:
        inputs=out/condition;create(inputs,11,9,6,condition)
        raw=(inputs/'report.json').read_bytes()
        before={p.name:sha(p.read_bytes()) for p in inputs.iterdir()}
        for policy,fn in FUNCS.items():
            data=canon(fn(raw,inputs,compact=False));(out/(condition+'-'+policy+'.json')).write_bytes(data)
        after={p.name:sha(p.read_bytes()) for p in inputs.iterdir()}
        allrows.append({'condition':condition,'before':before,'after':after})
    (out/'RECORD.json').write_bytes(canon({'pid':os.getpid(),'argv':sys.argv,'rows':allrows}))
    check_sources();print(json.dumps({'controls':len(allrows),'pid':os.getpid()}),flush=True)


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='controls': controls(sys.argv[2])
    elif mode=='construction': run(sys.argv[2],{'id':'construction','width':17,'height':13,'level':6},3,1)
    elif mode=='formal':
        cfg=json.loads((ROOT/'PLAN.json').read_text());idx=int(sys.argv[2])
        run(sys.argv[3],cfg['conditions'][idx],cfg['pairs'],cfg['warmup_pairs'])
    else: raise ValueError(mode)
