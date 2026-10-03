"""One fresh saved-only successor; never invokes predecessor CLI or acquisition."""
import argparse
import copy
import hashlib
import importlib
import json
import sys
import traceback
from pathlib import Path
from adapter import normalize_launch

HERE=Path(__file__).resolve().parent
MUTATIONS=('wait_bool','cpu_false','missing_wait','post_after_paint','source_wait_id','pixel_hash',
           'mount_missing','mount_extra','mount_duplicate','mount_type','mount_source','mount_rw','mount_rw_int')

def pins(root, expected):
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    if actual!=set(expected): raise ValueError('closed predecessor file denominator')
    for name,digest in expected.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('predecessor byte pin '+name)

def baseline(predecessor):
    sys.path.insert(0,str(predecessor))
    module=importlib.import_module('auditor')
    if Path(module.__file__).resolve()!=predecessor/'auditor.py': raise ValueError('baseline import origin')
    original=module.admit_launch
    def successor(receipt, freeze):
        return original(normalize_launch(receipt,freeze),freeze)
    module.admit_launch=successor
    if any(name in sys.modules for name in ('probe','runner','fixture_trace','observer','policy','x11','timing')):
        raise ValueError('acquisition import forbidden')
    return module

def copy_trial(raw, trial):
    trial.mkdir(parents=True,exist_ok=False)
    for original in raw.rglob('*'):
        if original.is_file():
            target=trial/original.relative_to(raw)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(original.read_bytes())

def mutate(trial,name,read):
    cell=trial/'record'
    if name.startswith('mount_'):
        launch=read(trial/'launch.json');state=json.loads(launch['inspect_stdout']);mounts=state['Mounts']
        source=next(m for m in mounts if m['Destination']=='/src')
        if name=='mount_missing': state['Mounts']=[source]
        elif name=='mount_extra': mounts.append({'Type':'bind','Source':'/other','Destination':'/extra','RW':False})
        elif name=='mount_duplicate': state['Mounts']=[source,copy.deepcopy(source)]
        elif name=='mount_type': source['Type']='tmpfs'
        elif name=='mount_source': source['Source']='/wrong'
        elif name=='mount_rw': source['RW']=True
        elif name=='mount_rw_int': source['RW']=0
        else: raise ValueError('unknown control')
        launch['inspect_stdout']=json.dumps(state,sort_keys=True)
        launch['inspection']['stdout']=launch['inspect_stdout']
        (trial/'launch.json').write_text(json.dumps(launch,sort_keys=True)+'\n')
        return
    so,ca=read(cell/'source.json'),read(cell/'capture.json')
    if name=='wait_bool': so['wait_traces'][0]['wait']['return_ns']=False
    elif name=='cpu_false': so['wait_traces'][0]['post']['cpu_stat']['nr_throttled']=False
    elif name=='missing_wait': so['wait_traces'].pop()
    elif name=='post_after_paint': so['wait_traces'][0]['post']['end_ns']=so['events'][0]['draw_start_ns']+1
    elif name=='source_wait_id': so['wait_traces'][0]['id']=99
    elif name=='pixel_hash': ca['frames'][0]['pixel_sha256']='0'*64
    else: raise ValueError('unknown control')
    (cell/'source.json').write_text(json.dumps(so,sort_keys=True)+'\n')
    (cell/'capture.json').write_text(json.dumps(ca,sort_keys=True)+'\n')
    (cell/'source-waits.jsonl').write_text(''.join(json.dumps(t,sort_keys=True)+'\n' for t in so['wait_traces']))
    (cell/'frames.jsonl').write_text(''.join(json.dumps(f,sort_keys=True)+'\n' for f in ca['frames']))
    saved=read(cell/'cell.json')
    saved['files_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in cell.iterdir() if p.is_file() and p.name!='cell.json'}
    (cell/'cell.json').write_text(json.dumps(saved,sort_keys=True)+'\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--predecessor',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(exist_ok=False)
    controls=[]
    try:
        freeze=json.loads((HERE/'FREEZE.json').read_text())
        for name,digest in freeze['source_sha256'].items():
            if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=digest:
                raise ValueError('successor source pin '+name)
        predecessor=args.predecessor.resolve()
        pins(predecessor,freeze['predecessor_sha256'])
        module=baseline(predecessor)
        prior=module.ref.read(predecessor/'FREEZE.json')
        raw=predecessor/'native-raw'
        result=module.validate(raw,prior)
        for name in MUTATIONS:
            trial=args.out/'trials'/name
            copy_trial(raw,trial)
            mutate(trial,name,module.ref.read)
            try:
                module.validate(trial,prior)
            except (ValueError,KeyError,TypeError) as exc:
                controls.append({'mutation':name,'rejected':True,'reason':str(exc),'trial':'trials/'+name})
            else:
                raise ValueError('ineffective full-path control '+name)
        result.update({'allocation':'MOUNT-ADMISSION-7100-C01-20261003-3CBF',
                       'predecessor_status':'STOP_AUDITOR_LAUNCH_CUSTODY','predecessor_relabelled':False,
                       'native_producer_invocations':0,'successor_saved_verifier_invocations_declared':1,
                       'predecessor_official_auditor_reinvocations':0,'retry':0,'controls_rejected':len(controls),
                       'adapter_scope':'closed destination-keyed bind mount admission; original byte evidence unchanged',
                       'scope':'saved-only qualified finite instrumented B01 profile; not original A02 rootcause/phase efficacy/rare-tail/safety'})
        (args.out/'RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
        (args.out/'controls.json').write_text(json.dumps(controls,sort_keys=True,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ('decomposition','source_wait_metrics','observer_wait_metrics','structural_metrics')},sort_keys=True))
    except Exception:
        (args.out/'RESULT_STOP.json').write_text(json.dumps({'status':'STOP_SUCCESSOR_SAVED_VALIDATION',
            'first_failure':traceback.format_exc(),'controls_completed':controls,'retry':0,
            'native_producer_invocations':0,'predecessor_relabelled':False},sort_keys=True,indent=2)+'\n')
        raise

if __name__=='__main__': main()
