"""Recompute every reported result without running a GUI or importing frontier."""
import csv
import hashlib
import json
from pathlib import Path
import statistics
from audit import audit_case

HERE=Path(__file__).resolve().parent


def replay():
    plan=json.loads((HERE/'preregistration.json').read_text())
    for name,h in plan['source_sha256'].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h, name
    rows=[]
    for b in range(plan['blocks']):
        assert json.loads((HERE/f'results/block-{b}/plan.json').read_text())==plan
    paths=list((HERE/'results').glob('block-*/case-*'))
    assert len(paths)==plan['cases']==len(plan['schedule'])
    for spec in plan['schedule']:
        root=HERE/f'results/block-{spec["block"]}/case-{spec["index"]:03d}'
        result=json.loads((root/'result.json').read_text())
        assert result['spec']==spec
        row=audit_case(root)
        assert row['pass'],row
        assert row==json.loads((root/'audit.json').read_text())
        rows.append(row)
    policies={}
    for policy in sorted({r['policy'] for r in rows}):
        subset=[r for r in rows if r['policy']==policy]
        policies[policy]={k:sum(r[k] for r in subset) for k in
            ['effects','correct_effects','wrong_effects','premature_dependent_reads','input_releases','lookups','independent_before_A_resolution']}
        policies[policy].update(cases=len(subset), visible_complete=sum(r['visible_complete'] for r in subset),
                               exact_complete=sum(r['visible_complete'] and r['effects']==r['correct_effects']==4 for r in subset))
    pairs=[]
    for scenario in ('delayed','alias'):
        for rep in range(3):
            matched={r['policy']:r for r in rows if r['scenario']==scenario and r['repetition']==rep}
            base=matched['global_wait'];candidate=matched['frontier']
            assert base['visible_complete'] and candidate['visible_complete']
            assert base['correct_effects']==candidate['correct_effects']==4
            pairs.append(dict(scenario=scenario,repetition=rep,global_ms=base['duration_ms'],
                              frontier_ms=candidate['duration_ms'],reduction_ms=base['duration_ms']-candidate['duration_ms'],
                              ratio=candidate['duration_ms']/base['duration_ms']))
    def distribution(values):
        return dict(n=len(values),median=statistics.median(values),min=min(values),max=max(values))
    comparison={k:distribution([p[k] for p in pairs]) for k in ('global_ms','frontier_ms','reduction_ms','ratio')}
    gates={
        'all_75_case_audits':len(rows)==75 and all(r['pass'] for r in rows),
        'candidate_wrong_effects_zero':all(r['wrong_effects']==0 for r in rows if r['policy'] in ('frontier','frontier_lookup')),
        'six_frontier_pairs_do_two_independent_tasks_early':all(r['independent_before_A_resolution']==2 for r in rows if r['policy']=='frontier' and r['scenario'] in ('delayed','alias')),
        'three_lost_ack_lookups_complete':all(r['visible_complete'] and r['correct_effects']==4 for r in rows if r['policy']=='frontier_lookup' and r['scenario']=='ack_lost'),
        'three_dropped_requests_remain_unknown':all(not r['visible_complete'] and r['acknowledged']==2 and r['correct_effects']==2 for r in rows if r['policy']=='frontier_lookup' and r['scenario']=='dropped'),
        'paired_median_ratio_at_most_0_8':comparison['ratio']['median']<=.8}
    summary=dict(schema='pending-effect-frontier-summary-v1',allocation_id=plan['allocation_id'],
                 base_commit=plan['base_commit'],preregistration_commit='734a07200b1bdd130dc3873838e459f6329fc10c',
                 cases=len(rows),test_count_prefreeze=39,finite_effect_pairs_tested=4096,
                 input_releases=sum(r['input_releases'] for r in rows),
                 acquisition_brackets=sum(r['acquisition_brackets'] for r in rows),
                 policies=policies,paired_comparison=comparison,pairs=pairs,gates=gates,
                 pass_all=all(gates.values()),environment=json.loads((HERE/'results/block-0/environment.json').read_text()),
                 interpretation='Scoped native-GUI calibration only; controls include intentional semantic failures. Structured effects/aliases/status are explicit extra contracts. Not runtime/model/Doom/general speed evidence.')
    return rows,summary


if __name__=='__main__':
    rows,summary=replay()
    (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    fields=[k for k in rows[0] if k not in ('failures','pass')]
    with (HERE/'results/cases.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    print(json.dumps(summary,indent=2,sort_keys=True))
