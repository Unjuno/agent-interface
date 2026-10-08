import copy
import json
import sys
import tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import candidate
import auditor

def audit_object(fixture,out):
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'candidate.json'
        path.write_text(json.dumps(out),encoding='utf-8')
        return auditor.audit(HERE/'fixture.json',path)

def main():
    f=json.loads((HERE/'fixture.json').read_text(encoding='utf-8'))
    assert len(f['decision_pairs'])==6
    assert len(f['budgets'])==4 and sum(x is not None for x in f['budgets'])==3
    out=candidate.run(HERE/'fixture.json')
    baseline=audit_object(f,out)
    assert baseline['decision']=='METHOD_PASS_SCOPED',baseline
    assert baseline['offered_trial_rows']==32 if 'offered_trial_rows' in baseline else baseline['observed_trial_rows']==32
    statuses=baseline['decision_statuses']
    assert statuses['equivalent_fast_route']=='ACCEPTED_EQUIVALENT'
    assert statuses['equivalent_tie_rule']=='ACCEPTED_EQUIVALENT'
    assert statuses['verification-crosses-short-deadline']=='REJECTED_FALSE_EQUIVALENCE'
    assert statuses['lease-expires']=='REJECTED_CONTEXT_MISMATCH'
    assert statuses['intent-changed']=='REJECTED_CONTEXT_MISMATCH'
    assert statuses['genuine-slack-sensitive']=='ACCEPTED_SLACK_SENSITIVE'
    assert baseline['surface_patterns']=={'planted_rank_reversal':'RANK_REVERSAL','no_interaction_null':'NO_INTERACTION_NULL'}
    impossible=next(x for x in out['decision_pairs'] if x['id']=='verification-crosses-short-deadline')
    assert next(x for x in impossible['variants'] if x['variant']=='short')['choice']=='YIELD'

    mutations=[]
    def reject(name,mutator):
        corrupted=copy.deepcopy(out); mutator(corrupted)
        result=audit_object(f,corrupted)
        mutations.append((name,result['decision']))
    reject('drop_late_and_abstained_rows',lambda x:x.update(trial_rows=[r for r in x['trial_rows'] if r['card'] not in ('correct_late','abstain')] ))
    def proposal_proxy(x):
        row=next(r for r in x['trial_rows'] if r['card']=='correct_late' and r['budget']==7)
        row['effect_by_deadline']=row['proposal_by_deadline']
        row['correct_effect_by_deadline']=row['proposal_by_deadline']
    reject('proposal_substituted_for_effect',proposal_proxy)
    def shift_clock(x):
        next(r for r in x['trial_rows'] if r['card']=='correct_fast' and r['budget']==5)['clock']='wall-clock-domain'
    reject('shift_clock_domain',shift_clock)
    reject('accept_false_slack_equivalence',lambda x:next(r for r in x['decision_pairs'] if r['id']=='verification-crosses-short-deadline').update(status='ACCEPTED_EQUIVALENT'))
    assert all(result=='FAIL_METHOD' for _,result in mutations),mutations
    print(json.dumps({'construction':'PASS','decision_tasks':6,'decision_trials':32,
                      'invalid_controls_rejected':len(mutations),'mutation_results':dict(mutations),
                      'decision_statuses':statuses,'surface_patterns':baseline['surface_patterns']},sort_keys=True))

if __name__=='__main__': main()
