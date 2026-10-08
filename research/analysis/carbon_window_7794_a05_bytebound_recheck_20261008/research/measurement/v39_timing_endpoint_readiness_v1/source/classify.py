import json
from pathlib import Path
INTERVALS = {
    'planner_wait': ('planner_request','planner_response'),
    'response_to_accept': ('planner_response','action_accept'),
    'accept_to_input_ack': ('action_accept','input_ack'),
    'input_to_useful': ('input_ack','first_useful_effect'),
    'observation_to_useful': ('observation_ready','first_useful_effect'),
    'useful_to_terminal': ('first_useful_effect','terminal_verified'),
}
RECORDED='RECORDED'

def classify(m):
    clock_ok = m['clock_provenance']['clock_domain_retained'] and m['clock_provenance']['clock_epoch_retained']
    rows={}
    for name,(a,b) in INTERVALS.items():
        ea,eb=m['endpoints'][a],m['endpoints'][b]
        reasons=[]
        if ea['status'] != RECORDED: reasons.append(f'{a}:{ea["status"]}')
        if eb['status'] != RECORDED: reasons.append(f'{b}:{eb["status"]}')
        if not clock_ok: reasons.append('CLOCK_PROVENANCE_MISSING')
        rows[name]={'reportable':not reasons,'reasons':reasons}
    ready=all(x['reportable'] for x in rows.values())
    return {'decision':'READY_RETAINED_V39_TIMING_ENDPOINTS_SCOPED' if ready else 'BLOCKED_RETAINED_V39_TIMING_ENDPOINTS',
            'intervals':rows,'reportable_count':sum(x['reportable'] for x in rows.values()),
            'total_intervals':len(rows),'clock_provenance_complete':clock_ok}

def main():
    m=json.loads(Path('source_map.json').read_text())
    out=classify(m); Path('../RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
