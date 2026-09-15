"""Recalculate the narrow retained endpoint decision with the standard library."""
import json, statistics
from pathlib import Path

def audit(path):
    data=json.loads(Path(path).read_text());columns=data['columns'];pairs={};valid=0;positive={}
    for row in data['rows']:
        r=dict(zip(columns,row))
        if not r['final_start_ns']<=r['final_sample_ns']<=r['final_end_ns']:
            raise ValueError('final payload outside bracket')
        if any(type(t) is not int or t<0 for t in r['refresh_call_durations_ns_before_deadline']):
            raise ValueError('invalid refresh duration')
        valid+=1
        positive.setdefault(r['mode'],[]).append(r['first_kill_observed_ns']<=r['deadline_ns'])
        pairs.setdefault(r['rep'],{})[r['mode']]=sum(r['refresh_call_durations_ns_before_deadline'])
    ratios=[p['refresh5']/p['refresh10'] for _,p in sorted(pairs.items())]
    median=statistics.median(ratios)
    return {'final_brackets_pass':valid,'positive_before_deadline':{k:sum(v) for k,v in positive.items()},
            'paired_ratios':ratios,'paired_ratio_median':median,'cost_gate_pass':median<=.65}
if __name__=='__main__':
    print(json.dumps(audit(Path(__file__).resolve().parent/'results/endpoints.json'),indent=2))
