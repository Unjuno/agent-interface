from __future__ import annotations
LABELS={
 'SUCCEEDED','IN_PROGRESS','BLOCKED','AUTHORITY_REQUIRED','TARGET_NOT_FOUND',
 'CAPABILITY_UNSUPPORTED','CONFLICT','IMPOSSIBLE_UNDER_CONSTRAINTS','FAILED_UNKNOWN'
}
def classify(e):
    # Complete exact success can be retained only when the effect receipt is singular and lineage-bound.
    effects=e.get('effect_receipts',[])
    if len(effects)>1 and len({x.get('value') for x in effects})>1:
        return out('CONFLICT',False,'reobserve_or_reconcile')
    if not e.get('evidence_complete',False):
        return out('FAILED_UNKNOWN',False,'new_observation')
    if not e.get('constraints_satisfiable',True):
        return out('IMPOSSIBLE_UNDER_CONSTRAINTS',False,'planner_reconsideration')
    if not e.get('capability_supported',True):
        return out('CAPABILITY_UNSUPPORTED',False,'different_action')
    if not e.get('target_present',True):
        return out('TARGET_NOT_FOUND',False,'new_target_or_observation')
    if not e.get('authority_current',True):
        return out('AUTHORITY_REQUIRED',False,'fresh_authority')
    if e.get('modal_blocking',False):
        return out('BLOCKED',False,'clear_blocker')
    if len(effects)==1 and effects[0].get('request_id')==e.get('request_id') and effects[0].get('value')=='DONE':
        return out('SUCCEEDED',False,'none')
    if e.get('input_dispatched') and e.get('app_request_seen') and e.get('pending_receipt'):
        return out('IN_PROGRESS',False,'wait_or_reobserve')
    return out('FAILED_UNKNOWN',False,'new_observation')
def out(label,retry,required):
    return {'label':label,'identical_retry_allowed':bool(retry),'required_change':required,'authority_granted':False}
def coarse(e):
    effects=e.get('effect_receipts',[])
    if any(x.get('value')=='DONE' for x in effects):
        return {'label':'SUCCESS','advice':'STOP'}
    if e.get('deadline_elapsed'):
        return {'label':'FAILED','advice':'STOP'}
    return {'label':'NO_EFFECT','advice':'RETRY_IDENTICAL'}
