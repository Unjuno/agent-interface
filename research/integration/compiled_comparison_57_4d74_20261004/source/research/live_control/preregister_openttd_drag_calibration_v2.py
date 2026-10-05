"""Freeze corrected zero-model OpenTTD drag calibration before execution."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/openttd-drag-calibration-02'
SOURCES = ['preregister_openttd_drag_calibration_v2.py', 'probe_openttd_drag_calibration_v2.py',
           'audit_openttd_drag_calibration_v2.py', 'pointer_socket_entry_v8.py', 'durable_submit_v4.py',
           'received_continuation_v1.py', 'received_exchange_v2.py', 'session_v22.py']
TASK = ['openttd_task/interactive_l_v1.py', 'openttd_task/guarded_l_score_v1.py',
        'openttd_task/results/l-geometry-01/baseline.sav']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


ROOT.mkdir(parents=True, exist_ok=False)
plan = {
    'study': 'openttd-drag-calibration-02',
    'status': 'PREREGISTERED_BEFORE_EXECUTION',
    'model_calls': 0,
    'offsets_y': [-16, -12, -8, -4, 0, 4],
    'base_points': [{'x': 705, 'y': 240}, {'x': 673, 'y': 256}, {'x': 641, 'y': 272}],
    'fixed_program': 'fresh observe; click known road toolbar; click known first directional road tool; one 600ms three-point drag; observe; independent finish',
    'target_tiles': [977, 978, 979, 1043, 1107],
    'comparison_evidence': {'offset_minus_16': 'model allocation v2 changed surrounding 912..915',
                            'offset_zero': 'model allocation v4 changed no scored tile',
                            'development_failure': 'calibration-01 rejected unsupported Shift_L+F8 before drag'},
    'primary_measurement': 'independent changed target and surrounding road-owner tiles per fresh restore',
    'decision_rule': 'use only to diagnose pixel-to-effect sensitivity; do not expose selected coordinates or engine result to a future planner',
    'scope': 'six fresh scripted episodes; no model judgment, autonomous targeting, task success, latency, token or general coordinate claim',
    'sources': {**{name: sha(HERE / name) for name in SOURCES},
                **{name: sha(HERE.parent / name) for name in TASK}},
}
temporary = ROOT / 'preregistration.json.tmp'
temporary.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
os.replace(temporary, ROOT / 'preregistration.json')
print(ROOT / 'preregistration.json')
