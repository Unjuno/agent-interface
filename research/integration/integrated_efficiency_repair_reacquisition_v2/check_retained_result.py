import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'integrated_efficiency_repair_reacquisition_v1'

def check():
    fixture = json.loads((ROOT / 'fixture.json').read_text())
    result = json.loads((ROOT / 'RESULT.json').read_text())
    assert fixture['allocation_id'] == 'integrated-efficiency-repair-reacquisition-v1'
    assert result['decision'] == 'PASS_REPAIR_REACQUISITION_ACCOUNTING_SCOPED'
    assert result['formal_invocation'] == 1
    assert result['formal_reruns'] == 0
    assert result['primary_comparator']['denominator_id'] == 'ephemeral.task4.layout_B.cold_reacquisition'
    assert result['primary_comparator']['numerator_id'] == 'persistent.task4.layout_B.repair'
    for name in ('durable_calls','input_tokens','local_observations','model_visible_images','output_tokens','planner_generations','reasoning_output_tokens'):
        ratio = result['ratios'][name]
        assert {'denominator','numerator','difference','ratio_decimal','ratio_fraction'} <= ratio.keys()
    return {'decision':'PASS_RETAINED_RESULT_PROVENANCE_SCOPED','fresh_allocation':False,'formal_invocation':result['formal_invocation']}

if __name__ == '__main__':
    print(json.dumps(check(), sort_keys=True))
