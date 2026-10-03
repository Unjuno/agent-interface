"""Saved-only audit. Imports no acquisition/fixture/producer/official predecessor CLI."""
import argparse
import copy
import hashlib
import json
import os
import statistics
from pathlib import Path
from validation import validate_cell

CELL_FILES={'spec.json','display-ready.json','fixture-ready.json','observer-ready.json',
            'epoch.json','source.json','capture.json','source.jsonl','source-waits.jsonl','frames.jsonl','waits.jsonl'} | {
            child+'.'+stream+'.log' for child in ('xvfb','fixture','observer') for stream in ('stdout','stderr')}

def unique(pairs):
    result={}
    for k,v in pairs:
        if k in result: raise ValueError('duplicate JSON field')
        result[k]=v
    return result
def read(path): return json.loads(Path(path).read_text(),object_pairs_hook=unique)
def write(path,value):
    with Path(path).open('x') as f: json.dump(value,f,sort_keys=True); f.write('\n')
def tree(root):
    result={}
    for p in sorted(root.rglob('*')):
        if p.is_symlink(): raise ValueError('symlink in retained raw')
        if p.is_file(): result[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return result
def expected_cases():
    cases=[]
    for kind in ('dark','persistent'):
        for t in ('full','minimal'):
            cases.append({'id':kind+'_'+t,'kind':kind,'treatment':t,'pair':None,
                          'phase':1,'width_ms':10,'offsets':[0,3,6,9]})
    for pair,order in enumerate((('full','minimal'),('minimal','full'),('minimal','full'),
                                  ('full','minimal'),('full','minimal'),('minimal','full'))):
        for t in order:
            cases.append({'id':'p'+str(pair)+'_'+t,'kind':'pulse','treatment':t,'pair':pair,
                          'phase':1,'width_ms':10,'offsets':[0,3,6,9]})
    return cases
def data_for(root):
    cell=read(root/'cell.json')
    data={'source':read(root/'source.json'),'capture':read(root/'capture.json'),'lifecycle':cell['lifecycle']}
    for key,name in [('epoch','epoch.json'),('fixture_ready','fixture-ready.json'),
                     ('observer_ready','observer-ready.json'),('display_ready','display-ready.json')]:
        data[key]=read(root/name)
    for key,name in (('source_journal','source.jsonl'),('source_waits','source-waits.jsonl'),
                     ('frames','frames.jsonl'),('observer_waits','waits.jsonl')):
        data[key]=[json.loads(s,object_pairs_hook=unique) for s in (root/name).read_text().splitlines()]
    return data
def check_cell(root,spec,native_root=None):
    saved=read(root/'cell.json')
    if saved['error'] is not None or saved['spec']!=spec or read(root/'spec.json')!=spec:
        raise ValueError('frozen cell specification/error')
    if (set(saved['files_sha256'])!=CELL_FILES or set(p.name for p in root.iterdir())!=CELL_FILES|{'cell.json'} or
        any(p.is_symlink() or not p.is_file() for p in root.iterdir())):
        raise ValueError('fixed complete cell file schema')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()
            if p.is_file() and p.name!='cell.json'}
    if hashes!=saved['files_sha256']: raise ValueError('closed cell file hash identity')
    data=data_for(root)
    command_root=root if native_root is None else native_root
    commands=saved['commands']; display=data['display_ready']['display']; xv=commands['xvfb']
    if (set(commands)!={'fixture','observer','xvfb'} or len(xv)!=10 or
        not isinstance(xv[2],str) or not xv[2].isdigit() or int(xv[2])<3 or
        xv!=['Xvfb','-displayfd',xv[2],'-screen','0','64x64x24','-nolisten','tcp','-noreset','-ac']):
        raise ValueError('private Xvfb argv/displayfd identity')
    expected_fixture=['/usr/local/bin/python3','-B','/source/fixture.py','--display',display,
        '--cell',str(command_root/'spec.json'),'--out',str(command_root)]
    expected_observer=['/usr/local/bin/python3','-B','/source/observer.py','--display',display,
        '--window',str(data['source']['window']),'--offsets',json.dumps(spec['offsets']),
        '--out',str(command_root),'--epoch-file',str(command_root/'epoch.json')]
    if commands['fixture']!=expected_fixture or commands['observer']!=expected_observer:
        raise ValueError('exact native child command/display custody')
    if read(root/'epoch.json')['epoch_ns']!=data['source']['epoch_ns']:
        raise ValueError('common epoch receipt')
    if (read(root/'fixture-ready.json')!={'pid':data['source']['pid'],'window':data['source']['window']} or
        read(root/'observer-ready.json')!={'pid':data['capture']['pid'],'initial_keymap':'00'*32}):
        raise ValueError('readiness child identity')
    return validate_cell(spec,data)

def independent_contrast(metrics):
    medians={}; pooled={'full':[],'minimal':[]}
    for m in metrics:
        if m['kind']!='pulse': continue
        values=[e['delay_ns'] for e in m['events']]
        medians[m['pair'],m['treatment']]=statistics.median(values)
        pooled[m['treatment']].extend(values)
    if len(medians)!=12 or any(len(v)!=48 for v in pooled.values()):
        raise ValueError('independent paired budget')
    differences=[medians[i,'full']-medians[i,'minimal'] for i in range(6)]
    reduction=statistics.median(pooled['full'])-statistics.median(pooled['minimal'])
    count=sum(d>=500_000 for d in differences)
    return {'status':'SUPPORTED_FINITE_CONTRAST' if reduction>=500_000 and count>=5 else 'HOLD_NOT_REPRODUCED',
            'paired_reductions_ns':differences,'pooled_reduction_ns':reduction}

def negative_controls(root,spec,base):
    trials=[]
    for name in ('dropped-frame','pixel-digest','draw-clock','omitted-full-snapshot','treatment',
                 'child-exit','epoch','source-deadline','missing-cpu-counter'):
        data=copy.deepcopy(base)
        if name=='dropped-frame': data['capture']['frames'].pop(); data['frames'].pop()
        elif name=='pixel-digest':
            data['capture']['frames'][0]['pixel_sha256']='0'*64; data['frames'][0]['pixel_sha256']='0'*64
        elif name=='draw-clock':
            start=data['source']['wait_traces'][0]['wait']['return_ns']-1
            data['source']['events'][0]['draw_start_ns']=start
            data['source']['wait_traces'][0]['paint_start_ns']=start
            data['source_waits'][0]['paint_start_ns']=start
            data['source_journal'][0]['start']=start
        elif name=='omitted-full-snapshot':
            data['source']['wait_traces'][0]['post']=None; data['source_waits'][0]['post']=None
        elif name=='treatment': data['source']['treatment']='minimal'
        elif name=='child-exit': data['lifecycle']['fixture_exit']=2
        elif name=='epoch': data['capture']['epoch_ns']+=1
        elif name=='source-deadline':
            data['source']['events'][0]['onset_ns']+=1
            data['source']['wait_traces'][0]['due_ns']+=1; data['source_waits'][0]['due_ns']+=1
        else:
            del data['source']['wait_traces'][0]['pre']['cpu_stat']['usage_usec']
            del data['source_waits'][0]['pre']['cpu_stat']['usage_usec']
        artifact=root/(name+'.json'); write(artifact,{'spec':spec,'data':data})
        try: validate_cell(spec,data)
        except (ValueError,KeyError,TypeError) as exc:
            trials.append({'name':name,'status':'REJECTED','reason':str(exc),
                           'sha256':hashlib.sha256(artifact.read_bytes()).hexdigest()})
        else: raise ValueError('real semantic cell corruption accepted: '+name)
    return trials

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--raw',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); ap.add_argument('--freeze',type=Path,required=True)
    a=ap.parse_args(); freeze=read(a.freeze); source=a.freeze.parent; before=tree(a.raw)
    for name,digest in freeze['source_sha256'].items():
        if hashlib.sha256((source/name).read_bytes()).hexdigest()!=digest: raise ValueError('source freeze mismatch')
    plan=expected_cases()
    if freeze['cases']!=plan or read(source/'plan.json')!=plan: raise ValueError('independent plan identity')
    raw=read(a.raw/'raw.json'); consumed=read(a.raw/'consumed.json')
    limits={'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'}
    actual={n:Path('/sys/fs/cgroup',n).read_text().strip() for n in limits}
    ids=[s['id'] for s in plan]
    if (raw['status']!='COMPLETE_DIAGNOSTIC' or raw['allocation']!=freeze['allocation'] or
        consumed['allocation']!=freeze['allocation'] or raw['cells']!=ids or raw['started_cells']!=ids or
        raw['source_sha256']!=freeze['source_sha256'] or raw['cgroups']!=limits or actual!=limits or
        type(raw['input_events']) is not int or raw['input_events']!=0 or
        type(raw['model_calls']) is not int or raw['model_calls']!=0):
        raise ValueError('complete diagnostic allocation/runtime boundary')
    if sorted(p.name for p in (a.raw/'cells').iterdir())!=sorted(ids): raise ValueError('closed cells')
    if set(before)!={'consumed.json','raw.json'} | {'cells/'+s['id']+'/'+name
            for s in plan for name in CELL_FILES|{'cell.json'}}:
        raise ValueError('closed raw file set')
    if freeze['native_output']!='/out/record': raise ValueError('frozen native output path')
    metrics=[check_cell(a.raw/'cells'/s['id'],s,Path(freeze['native_output'])/'cells'/s['id']) for s in plan]
    decision=independent_contrast(metrics)
    if metrics!=raw['metrics'] or decision!=raw['decision']: raise ValueError('saved independent arithmetic agreement')
    a.out.mkdir(exist_ok=False); (a.out/'controls').mkdir()
    spec=next(s for s in plan if s['kind']=='pulse' and s['treatment']=='full')
    controls=negative_controls(a.out/'controls',spec,data_for(a.raw/'cells'/spec['id']))
    if tree(a.raw)!=before: raise ValueError('saved raw changed during audit')
    write(a.out/'RESULT.json',{'status':'PASS_SAVED_DIAGNOSTIC_AUDIT','allocation':freeze['allocation'],
        'scientific_status':decision['status'],'decision':decision,'cells':16,'captures':128,
        'source_events':98,'source_waits':196,'input_events':0,'model_calls':0,
        'metrics':metrics,'controls':controls,'raw_sha256':before,'source_sha256':freeze['source_sha256'],
        'audit_cgroups':actual,'pid':os.getpid(),
        'scope':'finite instrumentation-cost diagnostic; shared collection validator, independently coded contrast arithmetic; controls are semantic CELL only, not full wrapper/custody attacks; no114phase-effect/rootcause/task/safety promotion'})

if __name__=='__main__': main()
