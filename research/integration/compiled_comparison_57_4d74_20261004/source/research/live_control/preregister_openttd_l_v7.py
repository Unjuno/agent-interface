"""Freeze the OpenTTD bounded drag-effect allocation before execution."""
import hashlib
import json
import os
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/timing-envelope-openttd-l-07'
SOURCES = [
    'preregister_openttd_l_v7.py',
    'timing_envelope_openttd_l_supervisor_v7.py',
    'timing_envelope_openttd_l_driver_v5.py',
    'openttd_effect_sheet_v1.py',
    'openttd_contact_sheet_v1.py',
    'openttd_drag_effect_v1.py',
    'openttd_finish_outcome_v1.py',
    'timing_envelope_v1.py',
    'timing_envelope_v2.py',
    'semantic_checkpoint_v4.py',
    'model_pair_runner_v2.py',
    'pointer_socket_entry_v8.py',
    'session_v22.py',
    'results/timing-envelope-openttd-l-06/posthoc-audit.json',
    'results/timing-envelope-openttd-l-06/drag-effect-audit.json',
]
TASK_SOURCES = [
    'openttd_task/interactive_l_v1.py',
    'openttd_task/guarded_l_score_v1.py',
    'openttd_task/observer_l_v1/common.nut',
    'openttd_task/observer_l_v1/main.nut',
    'openttd_task/observer_l_v1/info.nut',
    'openttd_task/results/l-geometry-01/baseline.sav',
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


ROOT.mkdir(parents=True, exist_ok=False)
plan = {
    'study': 'timing-envelope-openttd-l-07',
    'status': 'PREREGISTERED_BEFORE_EXECUTION',
    'execution_order': ['fixed-astra-effect-sheet'],
    'comparison_baseline': {
        'study': 'timing-envelope-openttd-l-06',
        'model': 'gpt-6-astra',
        'effort': 'medium',
        'hard_success': False,
        'model_turns': 12,
        'input_tokens': 199613,
        'repeated_same_A_to_B_drags': 2,
        'observer_outcome': 'partial_A_to_B_only',
    },
    'held_constant': {
        'seed': 991003,
        'save_sha256': 'c91ea76b4dc8c280f98de2e3a4c9b34d6033c833a34fc401bd0c076a15b4bc5b',
        'objective': 'five-tile L, ordered A-to-B horizontal then B-to-C vertical',
        'target_tiles': [977, 978, 979, 1043, 1107],
        'forbidden_tiles': [1041, 1042, 1105, 1106],
        'initial_ui': 'closed toolbar; one interface-owned Ctrl+2 tree transparency transition',
        'model_route': 'all gpt-6-astra medium',
        'max_model_turns': 12,
        'checkpoint_and_sign_semantics': 'same as v6',
        'evaluator': 'geometry-derived independent guarded_l_score_v1',
    },
    'intervention': 'after a pointer_drag, append bounded labeled before/after/absolute-RGB-difference crops below the current full frame for the next planner call',
    'primary_endpoints': [
        'independent hard success',
        'repeated same A-to-B drag count after first A-to-B effect',
        'model turns to independent terminal',
        'actual input and cached input tokens',
    ],
    'decision_rule': 'retain as a candidate only if independent correctness is preserved and repeated completed-segment work, planner boundaries, or actual tokens improve; one episode cannot promote a general speedup',
    'failure_policy': 'retain the first execution and every model/action/evaluator failure; no automatic retry',
    'negative_control_basis': 'unchanged task/runtime/evaluator negative controls already pass in v6 and driver-v5 bounded-finish probe; this allocation changes only planner presentation after drag',
    'scope': 'one fresh same-task interface comparison; no geometry generalization, latency distribution, human comparison, product or cross-domain claim',
    'sources': {**{name: digest(HERE / name) for name in SOURCES},
                **{name: digest(HERE.parent / name) for name in TASK_SOURCES}},
}
path = ROOT / 'preregistration.json'
temporary = path.with_suffix('.json.tmp')
temporary.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
os.replace(temporary, path)
print(path)
