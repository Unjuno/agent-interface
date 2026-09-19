from current_method import execute_handles

class RecoveryRejected(Exception): pass

def validate_recovery(r, expected_current='B'):
    if r.get('authority') != 'none' or r.get('task_input_granted') is not False:
        raise RecoveryRejected('authority')
    if r.get('focus') != expected_current or r.get('surface') != expected_current:
        raise RecoveryRejected('stale')
    g=r.get('geometry')
    if not (isinstance(g,list) and len(g)==4 and all(type(x) is int for x in g)):
        raise RecoveryRejected('geometry')
    return r

def execute_with_policy(client, task, aliases, policy):
    before_submits=len(client.submit_calls)
    baseline=execute_handles(client,task,aliases)
    after_submits=len(client.submit_calls)
    original_program=client.last_program
    if policy=='current_generic_yield':
        return dict(result=baseline,recovery_queries=0,post_rejection_task_submits=0,
                    original_submit_delta=after_submits-before_submits)
    if policy!='focus_recovery_adapter': raise ValueError(policy)
    rejected_reason=original_program['terminal'].get('reason')
    if baseline.get('status')!='safe_yield' or rejected_reason!='focus_mismatch':
        return dict(result=baseline,recovery_queries=0,post_rejection_task_submits=0,
                    original_submit_delta=after_submits-before_submits)
    recovery=validate_recovery(client.observe_only())
    enriched=dict(baseline)
    enriched['reason']='focus_mismatch'
    enriched['recovery_context']=recovery
    final_submits=len(client.submit_calls)
    return dict(result=enriched,recovery_queries=client.recovery_queries,
                post_rejection_task_submits=final_submits-after_submits,
                original_submit_delta=after_submits-before_submits)
