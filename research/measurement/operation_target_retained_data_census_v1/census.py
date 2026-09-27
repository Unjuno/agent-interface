import json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load_fixture():
    return json.loads((HERE/'fixture.json').read_text())

def evaluate(f):
    r=f['eligibility_requirements']; o=f['observed_contract']
    checks={
      'positive_rows': o['positive_rows'] >= r['min_positive_rows'],
      'semantic_negative_rows': o['semantic_negative_rows'] >= r['min_semantic_negative_rows'],
      'operation_classes': len(o['operation_classes']) >= r['min_operation_classes'],
      'target_alternatives': o['target_alternatives_per_operation'] >= r['min_target_alternatives_per_operation'],
      'yield_or_no_local_action_negatives': (not r['requires_yield_or_no_local_action_negatives']) or o['yield_or_no_local_action_negative_rows'] > 0,
      'operation_target_oracle': (not r['requires_independent_operation_target_semantic_oracle']) or o['independent_operation_target_semantic_oracle'] is True,
      'leakage_free_split': (not r['requires_leakage_free_split_units']) or o['independent_split_units'] >= 2,
      'caller_visible_rows_present': o['caller_visible_source_rows'] > 0,
      'final_effect_oracle_present': o['independent_final_effect_oracle'] is True,
    }
    ready=all(checks.values())
    return {
      'decision':'READY_OPERATION_TARGET_SHADOW_CORPUS' if ready else 'BLOCKED_DATA',
      'checks':checks,
      'failed_requirements':[k for k,v in checks.items() if not v],
      'observed':o,
      'sources':f['sources'],
      'scope':'retained Golden Desktop v3 census only; no model inference or task input'
    }
