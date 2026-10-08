import json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(): return json.loads((HERE/'fixture.json').read_text())

def evaluate(f):
    families=f['families']; req=f['requirements']
    potential=sum(x['program_opportunities'] for x in families)
    split_units=sum(x['episode_units'] for x in families)
    raw_ops=sorted({o for x in families for o in x['operation_families']})
    qualified=[x for x in families if x['decision_operation_target_oracle']]
    qualified_rows=sum(x['program_opportunities'] for x in qualified)
    qualified_ops=sorted({o for x in qualified for o in x['operation_families']})
    negatives=sum(x['semantic_negative_rows'] for x in families)
    yield_rows=sum(x['explicit_yield_no_action_rows'] for x in families)
    checks={
      'positive_rows':qualified_rows>=req['min_positive_rows'],
      'semantic_negative_rows':negatives>=req['min_semantic_negative_rows'],
      'operation_classes':len(qualified_ops)>=req['min_operation_classes'],
      'target_alternatives':max((x.get('target_alternatives_per_state',0) for x in qualified),default=0)>=req['min_target_alternatives'],
      'yield_no_action':(not req['requires_yield_no_action']) or yield_rows>0,
      'decision_oracle':(not req['requires_decision_oracle']) or bool(qualified),
      'split_units':split_units>=req['min_split_units'],
      'raw_operation_diversity_present':len(raw_ops)>=2,
      'episode_final_oracles_present':all(x['episode_final_oracle'] for x in families),
    }
    return {
      'decision':'READY_CROSSDOMAIN_OPERATION_TARGET_CORPUS' if all(checks.values()) else 'BLOCKED_DATA',
      'checks':checks,
      'potential_program_opportunities':potential,
      'oracle_qualified_positive_rows':qualified_rows,
      'semantic_negative_rows':negatives,
      'yield_no_action_rows':yield_rows,
      'raw_operation_families':raw_ops,
      'oracle_qualified_operation_families':qualified_ops,
      'independent_episode_units':split_units,
      'failed_requirements':[k for k,v in checks.items() if not v],
      'nonlabels':f['nonlabels'],
      'sources':f['sources']
    }
