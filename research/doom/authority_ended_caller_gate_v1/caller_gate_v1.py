from __future__ import annotations
import copy, json, statistics, time
from pathlib import Path

SOURCE = Path('/tmp/lab/dual_lifetime/quiet-result.json')

# Baseline mirrors the permissive shape relevant to old callers: a terminal plus
# a scorer-consistent run is enough to move to the next semantic decision.
def legacy_replan_ready(r):
    return bool(r.get('terminal_status')) and r.get('score_agreement') is True

def gated_outcome(r, expected_steps=1):
    if r.get('release_verified') is not True or r.get('keys_down') != [] or r.get('buttons_down') != []:
        return 'BLOCK_RELEASE'
    if r.get('score_agreement') is not True:
        return 'BLOCK_SCORE'
    status = r.get('terminal_status')
    if status == 'completed':
        if r.get('steps_completed') == expected_steps:
            return 'PROGRAM_COMPLETED_REPLAN_READY'
        return 'BLOCK_COMPLETION_COUNT'
    if status != 'authority_ended':
        return 'BLOCK_STATUS'
    post = r.get('post_authority')
    if not isinstance(post, dict):
        return 'WAIT_POST_AUTHORITY_OBSERVATION'
    if r.get('post_release_input_admissions') != 0:
        return 'BLOCK_POST_RELEASE_INPUT'
    if post.get('grants_input_authority') is not False or post.get('tail_program_steps_resumed') != 0:
        return 'BLOCK_AUTHORITY_REVIVAL'
    if post.get('captures') != 1 or post.get('sequence_advanced') is not True or post.get('within_lifecycle_deadline') is not True:
        return 'WAIT_POST_AUTHORITY_OBSERVATION'
    return 'PARTIAL_EFFECT_REPLAN_READY'

def make_cases():
    data=json.loads(SOURCE.read_text())
    valid=[copy.deepcopy(r) for r in data['results'] if r['arm']=='quiet_hold']
    cases=[]
    for i,r in enumerate(valid):
        cases.append((f'valid-{i}', r, True, 'PARTIAL_EFFECT_REPLAN_READY'))
        x=copy.deepcopy(r);x['post_authority']=None
        cases.append((f'missing-post-{i}', x, False, 'WAIT_POST_AUTHORITY_OBSERVATION'))
        x=copy.deepcopy(r);x['post_release_input_admissions']=1
        cases.append((f'post-input-{i}', x, False, 'BLOCK_POST_RELEASE_INPUT'))
        x=copy.deepcopy(r);x['post_authority']['tail_program_steps_resumed']=1
        cases.append((f'tail-revived-{i}', x, False, 'BLOCK_AUTHORITY_REVIVAL'))
        x=copy.deepcopy(r);x['release_verified']=False
        cases.append((f'unverified-release-{i}', x, False, 'BLOCK_RELEASE'))
        x=copy.deepcopy(r);x['score_agreement']=False
        cases.append((f'score-disagree-{i}', x, False, 'BLOCK_SCORE'))
    return cases

def main():
    cases=make_cases();rows=[]
    for name,r,should_ready,expected in cases:
        legacy=legacy_replan_ready(r);gate=gated_outcome(r)
        gate_ready=gate.endswith('REPLAN_READY')
        rows.append({'case':name,'should_replan_ready':should_ready,'legacy_ready':legacy,'gated':gate,'gated_ready':gate_ready,'expected_gate':expected})
    assert all(x['gated']==x['expected_gate'] for x in rows)
    valid=[x for x in rows if x['should_replan_ready']]
    faults=[x for x in rows if not x['should_replan_ready']]
    summary={
      'schema':'authority-ended-caller-gate-development-v1',
      'source':'quiet-result.json actual real-MAP01 result rows + one-fault-at-a-time injected copies',
      'n_valid':len(valid),'n_faults':len(faults),
      'legacy_valid_ready':sum(x['legacy_ready'] for x in valid),
      'legacy_fault_ready':sum(x['legacy_ready'] for x in faults),
      'gated_valid_ready':sum(x['gated_ready'] for x in valid),
      'gated_fault_ready':sum(x['gated_ready'] for x in faults),
      'rows':rows,
    }
    sample=cases[0][1]
    trials=200_000
    t=[]
    for _ in range(7):
        s=time.perf_counter_ns()
        for __ in range(trials):gated_outcome(sample)
        t.append((time.perf_counter_ns()-s)/trials)
    summary['gate_eval_ns_per_call']={'trials_per_repeat':trials,'repeats':7,'median':statistics.median(t),'min':min(t),'max':max(t)}
    out=Path('/tmp/lab/dual_lifetime/caller-gate-result.json');out.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
