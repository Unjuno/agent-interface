"""Strict compact planner evidence; valid outputs equal measured v1 outputs."""
import copy,json
from checkpoint_contract_v1 import valid_reply,validate as validate_contract
from planner_evidence_v1 import execution


def checkpoint(resolution):
    if (type(resolution) is not dict or set(resolution) != {'request_id','checkpoint','authority'} or
            resolution.get('authority') != 'none'):
        raise ValueError('resolved checkpoint evidence required')
    request_id=resolution['request_id'];record=resolution['checkpoint'];evidence=record.get('evidence')
    if type(evidence) is not dict:raise ValueError('checkpoint evidence required')
    contract=validate_contract(evidence.get('contract'))
    if not valid_reply(record,contract,request_id):raise ValueError('invalid checkpoint evidence')
    status=evidence['status']
    result={'format':'planner-checkpoint-v1','request_id':request_id,'status':status,
            'contract':copy.deepcopy(contract),'reason':evidence.get('reason'),
            'observation_closed':False,'task_completion':'not_scored','authority':'none',
            'automatic_retry':'not_authorized'}
    if 'actual' in evidence:result['actual']=copy.deepcopy(evidence['actual'])
    if status=='VERIFIED':
        result['artifact_sha256']=evidence['artifact_sha256']
        result['next']='finish_only_if_declared_policy_accepts_this_scope'
    else:
        if evidence.get('error'):result['unavailable']={'type':evidence['error'].get('type')}
        result['next']='interpret_current_observation_then_require_fresh_admission'
    return result


def present(checkpoint_resolution,*,phase_report=None,prior_steps=None,recovered=False):
    view={'format':'planner-evidence-v1','checkpoint':checkpoint(checkpoint_resolution),
          'raw_evidence':'retained_by_caller','authority':'none'}
    if phase_report is not None:view['execution']=execution(phase_report)
    if prior_steps is not None:
        encoded=json.dumps(prior_steps,separators=(',',':'),allow_nan=False)
        if type(prior_steps) is not list or len(prior_steps)>10 or len(encoded)>4096:
            raise ValueError('bounded prior steps required')
        view['prior_steps']=copy.deepcopy(prior_steps)
    if recovered:
        view['delivery']={'query_reply':'recovered_by_command_free_original_id_read','query_resent':False}
    return view
