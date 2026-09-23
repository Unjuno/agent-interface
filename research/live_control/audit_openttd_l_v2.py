"""Audit the corrected preregistered OpenTTD L-objective failure."""
import hashlib,json
from pathlib import Path
import audit_openttd_matched_v2 as shared
from timing_envelope_v1 import interval,validate
HERE=Path(__file__).resolve().parent;BASE=HERE/'results/timing-envelope-openttd-l-02';shared.BASE=BASE
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    prereg=read(BASE/'preregistration.json');assert prereg['status']=='PREREGISTERED_BEFORE_EXECUTION' and prereg['execution_order']==['negative-control','fixed-astra']
    for name,digest in prereg['sources'].items():
        path=HERE.parent/name if name.startswith('openttd_task/') else HERE/name
        shared.source_with_hash(path,digest)
    fixture=read(HERE.parent/'openttd_task/results/l-geometry-01/audit.json');assert fixture['audit_passed'] and fixture['save_sha256']==prereg['task_allocation']['save_sha256']
    negative=read(BASE/'negative-control-supervisor/result.json');negative_failure=negative['failure_outcome'];assert negative['success'] and negative_failure['journal_calls']==0 and negative_failure['failure_mode']=='visual_verify_false_positive' and negative_failure['evaluation']['success'] is False
    arm=shared.audit_arm('fixed-astra');assert arm['hard_success'] is False and len(arm['model_turns'])==9 and arm['model_turns'][-1]['kind']=='verify'
    failure=read(BASE/'fixed-astra/failure-evaluation.json');assert failure['failure_mode']=='visual_verify_false_positive' and failure['proposals_executed']==8 and failure['journal_calls']==32 and failure['evaluation']['success'] is False
    checks=failure['evaluation']['checks'];assert checks=={'target_owned_roads':False,'ordered_bidirectional_connections':False,'forbidden_tiles_clear':True,'surrounding_road_owner_unchanged':False}
    assert failure['evaluation']['changed_surrounding_tiles']==[912,913,914,915]
    observation=read(BASE/'fixed-astra/runtime/evaluation.json')['observation'];indexed={tile['id']:tile for tile in observation['tiles']}
    assert [(indexed[t]['road'],indexed[t]['owner']) for t in [977,978,979,1043,1107]]==[(False,-1),(False,-1),(True,0),(True,0),(True,0)]
    assert observation['edges']==[[977,978,False,False],[978,979,False,False],[979,1043,True,True],[1043,1107,True,True]]
    typed=[read(BASE/f'fixed-astra/typed-{turn}.json') for turn in range(1,10)];drags=[step for proposal in typed for step in proposal.get('steps',[]) if step.get('op')=='pointer_drag'];assert len(drags)==2
    assert drags[0]['points']==[{'x':705,'y':224},{'x':673,'y':240},{'x':641,'y':256}] and drags[1]['points']==[{'x':641,'y':256},{'x':673,'y':272},{'x':705,'y':288}]
    timing=[validate(json.loads(line)) for line in (BASE/'fixed-astra-control/timing-envelope.jsonl').read_text().splitlines()]
    initial=next(row for row in timing if row['event']=='initial_observation_detected');visual=next(row for row in timing if row['event']=='verification_request_published');visual_interval=interval(initial,visual)
    arm['failure_mode']='visual_verify_false_positive';arm['initial_observation_to_semantic_completion_ms']=None;arm['visual_verify_request_ms']=visual_interval['duration_ns']/1e6;arm['visual_verify_request_uncertainty_ms']=visual_interval['uncertainty_ns']/1e6
    report={'audit_passed':True,'preregistered':True,'fixture':{'seed':fixture['seed'],'save_sha256':fixture['save_sha256'],'target':fixture['contract']['target'],'forbidden':fixture['contract']['forbidden']},
            'negative_control':{'passed':True,'model_calls':0,'durable_calls':0,'independent_success':False,'failure_mode':negative_failure['failure_mode']},
            'fixed_astra':arm,'engine_diagnosis':{'built_target_tiles':[979,1043,1107],'missing_target_tiles':[977,978],'connected_target_edges':[[979,1043],[1043,1107]],'missing_target_edges':[[977,978],[978,979]],'forbidden_tiles_clear':True,'changed_surrounding_tiles':[912,913,914,915],'model_drags':drags},
            'interpretation':'The B-to-C leg is correct. The intended A-to-B leg is absent and a four-tile road appears one map row above it. The exact cause is not instrumented; the drag at sign-label height and engine delta support a target-binding error as a hypothesis, not a proven cause.',
            'decision':'Do not promote the fixed route. Preserve the failure and test a generic magnified changed-region feedback candidate before another fresh allocation.',
            'scope':'one changed-objective episode; no success, general reliability, human comparison, latency distribution or speed claim','audit_sha256':sha(Path(__file__))}
    (BASE/'audit.json').write_bytes((json.dumps(report,indent=2)+'\n').encode('utf-8'));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
