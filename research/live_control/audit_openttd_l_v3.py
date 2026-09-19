"""Audit the preregistered OpenTTD semantic-checkpoint allocation."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
import audit_openttd_matched_v2 as shared
from append_checkpoint_v1 import inspect,load
from received_continuation_v1 import advance,start
from semantic_checkpoint_v1 import next_checkpoint_turn,parse
from timing_envelope_v1 import interval,validate
HERE=Path(__file__).resolve().parent;BASE=HERE/'results/timing-envelope-openttd-l-03'
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    prereg=read(BASE/'preregistration.json');assert prereg['status']=='PREREGISTERED_BEFORE_EXECUTION' and prereg['execution_order']==['negative-control','fixed-astra']
    for name,digest in prereg['sources'].items():
        path=HERE.parent/name if name.startswith('openttd_task/') else HERE/name
        shared.source_with_hash(path,digest)
    negative=read(BASE/'negative-control-supervisor/result.json');assert negative['success'] and negative['failure_outcome']['journal_calls']==0 and negative['failure_outcome']['evaluation']['success'] is False
    root=BASE/'fixed-astra';control=BASE/'fixed-astra-control';runtime=root/'runtime'
    for directory in (root,control):
        for name,digest in read(directory/'plan.json')['sources'].items():shared.source_with_hash(HERE/name,digest)
    manifest=read(runtime/'manifest.json');assert manifest['save_sha256']==prereg['task_allocation']['save_sha256']
    for name,digest in manifest['sources'].items():shared.source_with_hash(HERE.parent/name,digest)
    events=[json.loads(line) for line in (runtime/'events.jsonl').read_text().splitlines()];calls=read(root/'calls.json');endpoint=read(root/'endpoint.json');state=start(endpoint['socket'])
    def replay(exchange):
        nonlocal state
        request,reply=exchange['request'],exchange['reply'];assert request['after']==state['cursor'] and reply['records']==events[request['after']:reply['cursor']];state=advance(state,endpoint['socket'],request['after'],reply);expected=exchange['state']['continuation'] if 'state' in exchange else exchange['continuation'];assert state==expected
    replay(read(root/'initial.json'))
    for call in calls:replay(call['result']);assert call['result']['state']['pending'] is None
    assert load(root/'journal.jsonl')==calls[-1]['result']['state'];replay(read(root/'finish.json'))
    assert len(calls)==40
    required=None;models=[]
    for turn in range(1,11):
        model=root/f'model-{turn}';records=[json.loads(line) for line in (model/'events.jsonl').read_text().splitlines()];message=next(e['item']['text'] for e in records if e.get('type')=='item.completed');typed=parse(message,required);assert typed==read(root/f'typed-{turn}.json') and typed['kind']=='act'
        usage=next(e['usage'] for e in records if e.get('type')=='turn.completed');models.append({'turn':turn,'kind':'act','usage':usage});group=calls[(turn-1)*4:turn*4];assert [c['result']['request']['command']['op'] for c in group]==['clock','submit','clock','submit'];assert group[1]['result']['request']['command']['steps']==[{'op':'observe'}] and group[3]['result']['request']['command']['steps']==typed['steps']+[{'op':'observe'}]
        new=next_checkpoint_turn(turn,typed)
        if new is not None:required=new
        elif required is not None and typed['checkpoint']['status']=='observed':required=None
    assert required==5
    records=[json.loads(line) for line in (root/'model-11/events.jsonl').read_text().splitlines()];raw_stop=json.loads(next(e['item']['text'] for e in records if e.get('type')=='item.completed'));usage=next(e['usage'] for e in records if e.get('type')=='turn.completed');models.append({'turn':11,'kind':'stop','usage':usage});assert raw_stop['kind']=='stop' and raw_stop['checkpoint']['prior_turn']==5 and raw_stop['checkpoint']['status']=='uncertain'
    try:parse(json.dumps(raw_stop),required)
    except ValueError as error:assert str(error)=='verification requires observed pending effect'
    else:raise AssertionError('frozen v1 stop bug not reproduced')
    after_drag=[read(root/f'typed-{turn}.json') for turn in range(6,11)];assert all(p['intent']=='inspect' and p['checkpoint']['status']=='uncertain' and all(s['op'] not in {'pointer_click','pointer_drag'} for s in p['steps']) for p in after_drag)
    pointer_drags=[e for e in events if e.get('event')=='step_started' and e.get('operation')=='pointer_drag'];assert len(pointer_drags)==1
    artifacts=sorted(runtime.glob('*.ait'));observations=[e for e in events if e.get('event')=='observation'];assert len(artifacts)==len(observations);decoder=Decoder('live-control')
    for artifact,event in zip(artifacts,observations):
        decoded=decoder.accept(artifact.read_bytes())
        with Image.open(runtime/Path(event['image']).name) as image:assert (image.width,image.height,image.mode,image.tobytes())==(decoded.width,decoded.height,decoded.mode,decoded.pixels)
    terminals=[e for e in events if e.get('event')=='terminal'];assert terminals and all(e['release']['verified'] and not e['release']['keys_down'] and not e['release']['buttons_down'] for e in terminals)
    evaluation=read(runtime/'evaluation.json');assert evaluation['success'] is False and evaluation['changed_surrounding_tiles']==[912,913,914,915] and all(not tile['road'] for tile in evaluation['observation']['tiles'])
    failure=read(root/'failure-evaluation.json');assert failure['success'] is False and failure['proposals_executed']==10 and failure['journal_calls']==40
    assert read(control/'error.json')=={'type':'ValueError','detail':'verification requires observed pending effect','automatic_retry':False}
    timing=[validate(json.loads(line)) for line in (control/'timing-envelope.jsonl').read_text().splitlines()];assert [e['sequence'] for e in timing]==list(range(1,len(timing)+1))
    def per(event,turn):return next(e for e in timing if e['event']==event and e['details'].get('turn')==turn)
    model_intervals=[interval(per('planner_request_started',turn),per('planner_proposal_received',turn)) for turn in range(1,12)];feedback=[interval(per('proposal_published',turn),per('first_useful_feedback_detected',turn)) for turn in range(1,11)];stop_interval=interval(next(e for e in timing if e['event']=='initial_observation_detected'),per('planner_proposal_received',11))
    report={'audit_passed':True,'preregistered':True,'hard_success':False,'classification':'safe_model_stop_rejected_by_frozen_checkpoint_v1_bug','negative_control':{'passed':True,'model_calls':0,'durable_calls':0},'model_turns':models,'model_wait_total_ms':sum(v['duration_ns'] for v in model_intervals)/1e6,'proposal_to_useful_feedback_total_ms':sum(v['duration_ns'] for v in feedback)/1e6,'initial_observation_to_safe_stop_proposal_ms':stop_interval['duration_ns']/1e6,'input_tokens_total':sum(v['usage']['input_tokens'] for v in models),'cached_input_tokens_total':sum(v['usage']['cached_input_tokens'] for v in models),'runtime_exact_frames':len(observations),'contact_sheets':len(list(root.glob('planner-*.png'))),'durable_calls':len(calls),'append_records':inspect(root/'journal.jsonl')[1],'task_drags_started':1,'post_drag_mutations_started':0,'checkpoint_turn':5,'uncertain_inspection_turns':[6,7,8,9,10],'model_stop_turn':11,'independent_checks':evaluation['checks'],'changed_surrounding_tiles':evaluation['changed_surrounding_tiles'],'semantic_completion_ms':None,'failure_reason':'semantic_checkpoint_v1 incorrectly applied the observed-only verify rule to a safe stop; no retry','decision':'checkpoint prevented the second mutation and false verify, but did not complete or repair the task; fix safe-stop admission and typed failure packaging before reuse','scope':'one fresh candidate episode; no task success, broad correctness improvement, latency distribution, human comparison or speed claim','audit_sha256':sha(Path(__file__))}
    (BASE/'audit.json').write_bytes((json.dumps(report,indent=2)+'\n').encode('utf-8'));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
