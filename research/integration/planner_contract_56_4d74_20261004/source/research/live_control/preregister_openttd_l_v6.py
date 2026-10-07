"""Freeze the OpenTTD sign-to-tile semantic allocation before execution."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/timing-envelope-openttd-l-06'
SOURCES = [
    'preregister_openttd_l_v6.py',
    'openttd_negative_finish_l_v6.py',
    'audit_openttd_l_v6.py',
    'openttd_finish_outcome_v1.py',
    'timing_envelope_openttd_l_driver_v4.py',
    'timing_envelope_openttd_l_supervisor_v6.py',
    'timing_envelope_v1.py',
    'timing_envelope_v2.py',
    'semantic_checkpoint_v4.py',
    'model_pair_runner_v2.py',
    'pointer_socket_entry_v8.py',
    'session_v22.py',
    'openttd_contact_sheet_v1.py',
    'results/semantic-checkpoint-v4-probe.json',
    'results/timing-envelope-openttd-l-05/audit.json',
    'results/openttd-drag-calibration-02/audit.json',
    'results/openttd-tool-boundary-01/audit.json',
]
TASK_SOURCES = [
    'openttd_task/interactive_l_v1.py',
    'openttd_task/guarded_l_score_v1.py',
    'openttd_task/observer_l_v1/common.nut',
    'openttd_task/observer_l_v1/main.nut',
    'openttd_task/observer_l_v1/info.nut',
    'openttd_task/results/l-geometry-01/manifest.json',
    'openttd_task/results/l-geometry-01/audit.json',
    'openttd_task/results/l-geometry-01/baseline.sav',
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


ROOT.mkdir(parents=True, exist_ok=False)
plan = {
    'study': 'timing-envelope-openttd-l-06',
    'status': 'PREREGISTERED_BEFORE_EXECUTION',
    'execution_order': ['negative-control', 'fixed-astra'],
    'task_allocation': {
        'seed': 991003,
        'save_sha256': 'c91ea76b4dc8c280f98de2e3a4c9b34d6033c833a34fc401bd0c076a15b4bc5b',
        'target_tiles': [977, 978, 979, 1043, 1107],
        'forbidden_tiles': [1041, 1042, 1105, 1106],
        'objective': 'five-tile L, ordered A-to-B horizontal then B-to-C vertical',
        'toolbar': 'closed',
        'trees_before_interface': 'known opaque from fixed fixture contract',
        'trees_at_first_model_observation': 'transparent after exactly one interface-owned Ctrl+2 transition',
        'max_model_turns': 12,
        'evaluator': 'geometry-derived independent guarded_l_score_v1',
    },
    'negative_control': {
        'model_calls': 0,
        'view_only_durable_calls': 2,
        'pointer_or_task_mutation_steps': 0,
        'expected_engine_success': False,
        'expected_failure_mode': 'visual_verify_false_positive',
    },
    'positive_path': {
        'model_route': 'all turns gpt-6-astra medium',
        'interface_change': 'retain the v5 pre-action transparent view and add the general OpenTTD semantic fact that sign boxes annotate map squares, directing construction to the underlying tile surface without exposing calibrated coordinates',
        'official_semantic_source': 'https://wiki.openttd.org/en/Manual/Sign',
        'official_semantic_claim': 'OpenTTD signs are notes placed on map squares; visible sign boxes are annotations rather than the construction surface',
        'hard_success_gate': 'model verify plus independent evaluator success',
    },
    'primary_measurements': [
        'hard task success', 'pre-action transition duration',
        'first model observation to semantic completion or safe stop',
        'wrapper-observed model wait', 'proposal publication to first useful feedback',
        'model calls and reported token usage', 'durable calls and exact frames',
    ],
    'failure_policy': 'retain the first bounded, stopped, typed or independent failure and do not retry',
    'comparison_baseline': 'v5 same seed/task/model/checkpoint used pre-action transparency, stopped at turn 7, task false, 115045 input tokens; B-to-C was correct but A-to-B was one row high and model verification was false-positive',
    'version_reason': 'change only the planner semantic instruction from v5 to test whether a general sign-to-underlying-map-square relation corrects the repeated label-center targeting error',
    'interpretation_limit': 'one fixed-order candidate episode; known fixture view state only; no general state detection, correctness effect, latency distribution, human comparison or speedup claim',
    'sources': {**{name: digest(HERE / name) for name in SOURCES},
                **{name: digest(HERE.parent / name) for name in TASK_SOURCES}},
}
path = ROOT / 'preregistration.json'
temporary = path.with_suffix('.json.tmp')
temporary.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
os.replace(temporary, path)
print(path)
