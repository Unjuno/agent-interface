"""Finite source construction; invokes no operating backend."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from frozen_kernel import (Action,ActionKind,AuthorityLease,EffectOccurrence,
    EffectReceipt,EffectStatus,ExecutionReceipt,ExecutionRequest,Observation,
    ReleaseReceipt,RequestLifecycle,TargetBinding)

def signature(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)

def row(case):
    held=set();release_snapshot=None;press_seq=None;release_seq=None
    for event in case['events']:
        if event['kind']=='press':held.add(event['key']);press_seq=event['seq']
        elif event['kind']=='release':
            held.clear();release_snapshot=sorted(held);release_seq=event['seq']
    e=case['ended_ns'];r=case['release_ns']
    obs=Observation(1,1,'model-surface','0'*64,1,1,'synthetic')
    binding=TargetBinding('model-target',1,'model-surface','1'*64)
    lease=AuthorityLease('model-lease',1,'model-surface',5000,frozenset({ActionKind.KEY}))
    request=ExecutionRequest('modeled-one-press','2'*64,binding,lease,
        (Action('press-A',ActionKind.KEY,'model-key-down:A'),))
    receipt=ExecutionReceipt('modeled-one-press','model-release-'+str(e)+'-'+str(r),
        '2'*64,'model-lease',1,'model-surface',100,e,1,
        EffectOccurrence.OBSERVED,ReleaseReceipt(r,True,tuple(release_snapshot),()))
    flow=RequestLifecycle();flow.record_observation(obs);flow.bind(binding)
    flow.authorize(lease,now_ns=50);flow.begin_execution(request,now_ns=100)
    flow.record_execution(receipt)
    flow.record_effect(EffectReceipt('modeled-one-press','2'*64,e+300,
        EffectStatus.UNAVAILABLE,'3'*64))
    outcome=asdict(flow.outcome())
    projection=json.loads(signature(asdict(receipt)))
    return {'case_id':case['case_id'],
        'case_sha256':hashlib.sha256(signature(case).encode()).hexdigest(),
        'events':case['events'],'release_snapshot_keys_down':release_snapshot,
        'terminal_keys_down':sorted(held),'projection':projection,
        'kernel_outcome':json.loads(signature(outcome)),
        'comparators':{'end_floor':r>=e,'ordered_witness':press_seq<release_seq}}

def main():
    output=Path(sys.argv[1]);output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise FileExistsError('primary raw already exists')
    cases=json.loads((HERE/'cases.json').read_text(encoding='utf8'))['cases']
    freeze=(HERE/'FREEZE.json').read_bytes()
    for name,expected in json.loads(freeze)['sha256'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('frozen input mismatch: '+name)
    raw={'schema':'kernel-release-order-raw-v1',
        'freeze_sha256':hashlib.sha256(freeze).hexdigest(),
        'cases_sha256':hashlib.sha256((HERE/'cases.json').read_bytes()).hexdigest(),
        'source_identity':json.loads((HERE/'SOURCE.json').read_text(encoding='utf8')),
        'rows':[row(case) for case in cases]}
    output.write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print(json.dumps({'rows':len(raw['rows']),'raw_sha256':hashlib.sha256(output.read_bytes()).hexdigest()}))

if __name__=='__main__':main()
