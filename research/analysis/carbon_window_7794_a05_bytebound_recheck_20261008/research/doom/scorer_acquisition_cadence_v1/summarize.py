"""Post-run aggregation from retained events, not from hand-entered success counts."""
import argparse, json, statistics
from pathlib import Path
from audit import analyze, rows, stats

def summarize(evidence, runtime=None):
    here=Path(__file__).resolve().parent;plan=json.loads((here/'plan.json').read_text())
    cases=[analyze(Path(evidence)/s['id'],runtime,here) for s in plan['cases']]
    result={'schema':'scorer-acquisition-cadence-result-v1','cases':cases,'modes':{}}
    for mode in ['passive10','refresh10','refresh5']:
        cc=[c for c in cases if c['mode']==mode]
        result['modes'][mode]={'n':len(cc),'hard_pass':sum(c['hard_pass'] for c in cc),
            'before_deadline_positive':sum(c['positive_before_deadline'] for c in cc),
            'kill_results':[c['score']['kill_count'] for c in cc],
            'source_tic_counts':[c['distinct_source_tics_before_deadline'] for c in cc],
            'refresh_calls':sum(c['refresh_before_deadline_count'] for c in cc),
            'refresh_blocking_ms':stats([c['refresh_blocking_before_deadline_ms'] for c in cc]),
            'final_acquisition_ms':stats([c['final_acquisition_ms'] for c in cc]),
            'first_positive_after_admission_ms':stats([c['first_positive_after_admission_ms'] for c in cc if c['first_positive_after_admission_ms'] is not None]),
            'deadline_to_empty_ms':stats([c['deadline_to_empty_ms'] for c in cc])}
    pairs=[]
    for rep in range(1,7):
        a=next(c for c in cases if c['mode']=='refresh10' and c['rep']==rep)
        b=next(c for c in cases if c['mode']=='refresh5' and c['rep']==rep)
        pairs.append({'rep':rep,'ratio':b['refresh_blocking_before_deadline_ms']/a['refresh_blocking_before_deadline_ms'],
            'reduction_ms':a['refresh_blocking_before_deadline_ms']-b['refresh_blocking_before_deadline_ms'],
            'terminal_values_equal':a['score']==b['score'],
            'both_before_deadline':a['positive_before_deadline'] and b['positive_before_deadline']})
    result['pairs']=pairs
    result['paired_ratio']=stats([p['ratio'] for p in pairs]);result['paired_reduction_ms']=stats([p['reduction_ms'] for p in pairs])
    result['hard_pass']=all(c['hard_pass'] for c in cases)
    result['receipt_fix_pass']=result['hard_pass'] and all(c['final_payload_within_bracket'] for c in cases)
    result['cadence_gate_pass']=result['hard_pass'] and all(p['both_before_deadline'] and p['terminal_values_equal'] for p in pairs) and result['paired_ratio']['median']<=.65
    result['decision']={'receipt_fix':'PASS_VERSIONED_REAL_INTEGRATION' if result['receipt_fix_pass'] else 'FAIL',
        'cadence_reduction':'PASS_SCOPED_CANDIDATE' if result['cadence_gate_pass'] else 'HOLD_FROZEN_35_PERCENT_REDUCTION_GATE_NOT_MET',
        'shared_runtime_promotion':False,'gameplay_speedup_claim':False}
    result['totals']={k:sum(c[k] for c in cases) for k in ['acquisition_count','valid_acquisitions','heartbeat_count','missed_periods','controller_leak_count']}
    result['all_deadline_to_empty_ms']=stats([c['deadline_to_empty_ms'] for c in cases])
    return result

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('evidence',type=Path);a.add_argument('--runtime',type=Path);args=a.parse_args()
    print(json.dumps(summarize(args.evidence,args.runtime),indent=2,sort_keys=True))
