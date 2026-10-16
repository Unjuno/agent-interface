"""Audit the preregistered OpenTTD L-objective fixture and retained harness failure."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE/'results/timing-envelope-openttd-l-01'
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    prereg=read(BASE/'preregistration.json');assert prereg['status']=='PREREGISTERED_BEFORE_EXECUTION' and prereg['execution_order']==['negative-control','fixed-astra']
    for name,digest in prereg['sources'].items():
        path=HERE.parent/name if name.startswith('openttd_task/') else HERE/name
        assert sha(path)==digest,name
    fixture=read(HERE.parent/'openttd_task/results/l-geometry-01/audit.json');assert fixture['audit_passed'] and fixture['save_sha256']==prereg['task_allocation']['save_sha256']
    assert fixture['contract']['target']==prereg['task_allocation']['target_tiles'] and fixture['contract']['forbidden']==prereg['task_allocation']['forbidden_tiles']
    negative=read(BASE/'negative-control-supervisor/result.json');failure=negative['failure_outcome']
    assert negative['success'] and failure['success'] is False and failure['failure_mode']=='visual_verify_false_positive' and failure['journal_calls']==0 and failure['evaluation']['success'] is False
    control_error=read(BASE/'fixed-astra-control/error.json');assert control_error=={'type':'RuntimeError','detail':'driver exited before applied-1.json','automatic_retry':False}
    typed=read(BASE/'fixed-astra/typed-1.json');assert typed['kind']=='act' and typed['steps']==[{'op':'pointer_move','x':819,'y':51},{'op':'dwell_observe','delay_ms':800}]
    events=[json.loads(line) for line in (BASE/'fixed-astra/model-1/events.jsonl').read_text(encoding='utf-8').splitlines()]
    completed=next(e for e in events if e.get('type')=='turn.completed');usage=completed['usage'];assert usage['input_tokens']==15768
    calls=read(BASE/'fixed-astra/calls.json');assert [c['result']['request']['command']['op'] for c in calls]==['clock','submit','clock']
    assert calls[1]['result']['request']['command']['steps']==[{'op':'observe'}]
    runtime_events=[json.loads(line) for line in (BASE/'fixed-astra/runtime/events.jsonl').read_text(encoding='utf-8').splitlines()]
    pointer_starts=[e for e in runtime_events if e.get('event')=='step_started' and str(e.get('operation','')).startswith('pointer_')]
    assert pointer_starts==[] and not (BASE/'fixed-astra/result.json').exists() and not (BASE/'fixed-astra/failure-evaluation.json').exists()
    traceback=(BASE/'fixed-astra-control/driver-stderr.txt').read_text(encoding='utf-8');assert "submit/clock only; journal assigns unique identities" in traceback
    cleanup=read(BASE/'fixed-astra/runtime/cleanup.json');assert cleanup=={'all_owned_processes_exited':True,'save_unchanged':True}
    report={'audit_passed':True,'preregistered':True,'fixture':{'seed':fixture['seed'],'save_sha256':fixture['save_sha256'],'target':fixture['contract']['target'],'forbidden':fixture['contract']['forbidden']},
            'negative_control':{'passed':True,'model_calls':0,'durable_calls':0,'independent_success':False,'failure_mode':failure['failure_mode']},
            'positive_allocation':{'classification':'harness_failure_before_pointer_input','model_turns':1,'input_tokens':usage['input_tokens'],'cached_input_tokens':usage['cached_input_tokens'],'durable_calls':len(calls),'observation_only_submits':1,'pointer_steps_started':0,'semantic_outcome':'NOT_RECORDED','automatic_retry':False},
            'failure_reason':'caller supplied an action id to durable_submit_v4; the journal correctly rejected it because identities are assigned internally',
            'next_version':'timing_envelope_openttd_l_driver_v2.py restores the proven no-caller-id convention; requires a new preregistration and result root before model use',
            'scope':'fixture and packaging-path evidence; no OpenTTD L task success, model-control efficacy, latency or speed claim'}
    (BASE/'audit.json').write_bytes((json.dumps(report,indent=2)+'\n').encode('utf-8'));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
