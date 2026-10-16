"""Audit the preregistered static action-region visual diagnostic."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE/'results/openttd-l-action-region-diagnostic-01';REPO=HERE.parent.parent
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    plan=read(ROOT/'preregistration.json');assert plan['status']=='PREREGISTERED_BEFORE_MODEL_CALLS' and plan['execution_order']==['full-only','full-plus-action-region'] and plan['calls_per_condition']==1
    assert sha(ROOT/'prompt.txt')==plan['same_prompt_sha256'] and plan['hidden_scoring_reference']['expected_judgment']=='incorrect'
    for name,digest in plan['sources'].items():assert sha(HERE/name)==digest,name
    rows=[]
    for condition in plan['execution_order']:
        spec=plan['conditions'][condition];image=REPO/Path(spec['image'].replace('\\','/'));assert sha(image)==spec['sha256'] and image.stat().st_size==spec['bytes']
        result=read(ROOT/f'{condition}-result.json');assert result['condition']==condition and result['typed']['judgment'] in {'correct','incorrect','uncertain'}
        model=ROOT/condition;model_plan=read(model/'plan.json');assert model_plan['image_sha256']==spec['sha256'] and model_plan['requested_model']==plan['model'] and model_plan['requested_effort']==plan['effort']
        assert (model/'prompt.txt').read_text()==(ROOT/'prompt.txt').read_text() and read(model/'process.json')['exit_code']==0
        rows.append({'condition':condition,'judgment':result['typed']['judgment'],'rationale':result['typed']['rationale'],'input_tokens':result['usage']['input_tokens'],'cached_input_tokens':result['usage']['cached_input_tokens'],'output_tokens':result['usage']['output_tokens'],'reasoning_output_tokens':result['usage']['reasoning_output_tokens'],'image_bytes':spec['bytes']})
    assert [row['judgment'] for row in rows]==['uncertain','uncertain'];delta={key:rows[1][key]-rows[0][key] for key in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','image_bytes')}
    assert delta['input_tokens']==526 and delta['image_bytes']==40680
    report={'audit_passed':True,'preregistered':True,'conditions':rows,'composite_minus_full':delta,'expected_engine_judgment':'incorrect','decision':'reject action-region zoom alone as a diagnostic improvement in this trace; both calls remain uncertain while composite costs 526 more input tokens','next_candidate':'require an explicit semantic subgoal checkpoint before admitting the next mutation; the full image already supports uncertainty when the exact A-to-B alignment question is asked','scope':plan['scope']}
    (ROOT/'audit.json').write_bytes((json.dumps(report,indent=2)+'\n').encode('utf-8'));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
