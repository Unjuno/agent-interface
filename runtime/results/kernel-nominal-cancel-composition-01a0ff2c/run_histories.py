"""Fresh ordinary call histories; no backend, prior producer, or formal run."""
from pathlib import Path
from dataclasses import fields, is_dataclass, asdict
from enum import Enum
from types import SimpleNamespace
import hashlib, importlib.util, json, platform, sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
CASES = ['new', 'authorized_unbegun', 'begun_typed', 'begun_shaped_current',
         'begun_shaped_stale', 'begun_missing', 'begun_unrelated',
         'refused_begin', 'execution_none', 'execution_possible']
def normalized(x):
    if isinstance(x, Enum): return x.value
    if is_dataclass(x): return {f.name: normalized(getattr(x, f.name)) for f in fields(x)}
    if isinstance(x, dict): return {k: normalized(v) for k,v in x.items()}
    if isinstance(x, (tuple, list)): return [normalized(v) for v in x]
    if isinstance(x, (set, frozenset)): return sorted(normalized(v) for v in x)
    if x is None or type(x) in (str,int,bool): return x
    raise TypeError(type(x).__name__)
def attempt(call, flow):
    before = normalized(vars(flow))
    try:
        call()
        status, detail = 'returned', None
    except Exception as error:
        status, detail = type(error).__name__, str(error)
    return {'status': status, 'detail': detail, 'before': before, 'after': normalized(vars(flow))}
def load_kernel(arm):
    name = 'joint_kernel_' + arm
    folder = ROOT/'arms'/arm/'runtime/kernel'
    spec = importlib.util.spec_from_file_location(name, folder/'__init__.py', submodule_search_locations=[str(folder)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    for sub in ('contracts','backend','lifecycle'):
        assert Path(sys.modules[name+'.'+sub].__file__).resolve().parent == folder.resolve()
    return module
def history(k, case):
    digest = hashlib.sha256(b'joint-integration-fixed-input').hexdigest()
    flow = k.RequestLifecycle()
    observation = k.Observation(23,100,'joint-surface',digest,40,30,'rgb24')
    binding = k.TargetBinding('joint-target',23,'joint-surface',digest)
    lease = k.AuthorityLease('joint-lease',23,'joint-surface',2000,frozenset({k.ActionKind.KEY}))
    request = k.ExecutionRequest('joint-command',digest,binding,lease,(k.Action('joint-action',k.ActionKind.KEY,'Return'),))
    calls = []
    def call(name, fun):
        row = attempt(fun, flow); row['call'] = name; calls.append(row)
        return row['status']
    if case != 'new':
        call('observe', lambda:flow.record_observation(observation))
        call('bind', lambda:flow.bind(binding))
        call('authorize', lambda:flow.authorize(lease,now_ns=200))
    if case.startswith('begun_') or case.startswith('execution_'):
        call('begin', lambda:flow.begin_execution(request,now_ns=400))
    if case == 'refused_begin':
        call('expired_begin', lambda:flow.begin_execution(request,now_ns=2000))
    if case.startswith('execution_'):
        occurrence = k.EffectOccurrence.NONE if case.endswith('none') else k.EffectOccurrence.POSSIBLE
        receipt = k.ExecutionReceipt('joint-command','joint-backend',digest,'joint-lease',23,'joint-surface',600,800,1,occurrence,k.ReleaseReceipt(1000,True,(),()))
        call('execution',lambda:flow.record_execution(receipt))
    invalid = {
        'begun_shaped_current': lambda:SimpleNamespace(observed_ns=1000,released=True),
        'begun_shaped_stale': lambda:SimpleNamespace(observed_ns=399,released=True),
        'begun_missing':lambda:None,
        'begun_unrelated':lambda:object(),
    }
    if case in invalid:
        supplied = invalid[case]()
        status = call('invalid_stop',lambda:flow.stop('joint-cancel',release=supplied))
        if status != 'returned':
            call('valid_stop_after_refusal',lambda:flow.stop('joint-cancel',release=k.ReleaseReceipt(1000,True,(),())))
    elif case == 'new' or case.startswith('execution_'):
        call('valid_stop',lambda:flow.stop('joint-cancel'))
    else:
        call('valid_stop',lambda:flow.stop('joint-cancel',release=k.ReleaseReceipt(1000,True,(),())))
    outcome = attempt(flow.outcome, flow)
    result = normalized(flow.outcome()) if outcome['status']=='returned' else None
    return {'case':case,'calls':calls,'outcome_status':outcome['status'],'outcome':result}
def main():
    target = ROOT/'raw.json'
    assert not target.exists(), target
    start = datetime.now(timezone.utc).isoformat()
    binding_bytes = (ROOT/'SOURCE_BINDING.json').read_bytes()
    binding = json.loads(binding_bytes)
    rows = []
    for arm in binding['arms']:
        source = ROOT/'arms'/arm['name']/'runtime/kernel/lifecycle.py'
        assert hashlib.sha256(source.read_bytes()).hexdigest() == arm['lifecycle_sha256']
        module = load_kernel(arm['name'])
        for case in CASES:
            row = history(module,case)
            row.update(arm=arm['name'],nominal=arm['nominal'],uncertainty=arm['uncertainty'],lifecycle_sha256=arm['lifecycle_sha256'])
            rows.append(row)
    raw = {'schema':'kernel-nominal-cancel-composition-v1','started_utc':start,'ended_utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),'platform':platform.platform(),'source_binding_sha256':hashlib.sha256(binding_bytes).hexdigest(),'rows':rows}
    target.write_text(json.dumps(raw,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'rows':len(rows),'raw_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
if __name__ == '__main__': main()
