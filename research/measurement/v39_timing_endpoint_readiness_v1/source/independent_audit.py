import json,sys
from pathlib import Path
PAIRS=[('planner_wait','planner_request','planner_response'),('response_to_accept','planner_response','action_accept'),('accept_to_input_ack','action_accept','input_ack'),('input_to_useful','input_ack','first_useful_effect'),('observation_to_useful','observation_ready','first_useful_effect'),('useful_to_terminal','first_useful_effect','terminal_verified')]
def audit(map_path,result_path):
    m=json.loads(Path(map_path).read_text()); r=json.loads(Path(result_path).read_text()); errors=[]
    clock=bool(m['clock_provenance']['clock_domain_retained'] and m['clock_provenance']['clock_epoch_retained'])
    expected={}
    for n,a,b in PAIRS:
        reasons=[]
        if m['endpoints'][a]['status']!='RECORDED':reasons.append(f'{a}:{m["endpoints"][a]["status"]}')
        if m['endpoints'][b]['status']!='RECORDED':reasons.append(f'{b}:{m["endpoints"][b]["status"]}')
        if not clock:reasons.append('CLOCK_PROVENANCE_MISSING')
        expected[n]={'reportable':not reasons,'reasons':reasons}
    if r.get('intervals')!=expected:errors.append('interval_map')
    if r.get('reportable_count')!=sum(x['reportable'] for x in expected.values()):errors.append('count')
    if r.get('decision')!=('READY_RETAINED_V39_TIMING_ENDPOINTS_SCOPED' if all(x['reportable'] for x in expected.values()) else 'BLOCKED_RETAINED_V39_TIMING_ENDPOINTS'):errors.append('decision')
    if m['first_feedback_summary']['stronger_task_effect_all_admitted_plans'] is not False:errors.append('useful_effect_source')
    return {'pass':not errors,'errors':errors,'expected_reportable':sum(x['reportable'] for x in expected.values())}
if __name__=='__main__':
    v=audit(sys.argv[1],sys.argv[2]);print(json.dumps(v,sort_keys=True));raise SystemExit(0 if v['pass'] else 1)
