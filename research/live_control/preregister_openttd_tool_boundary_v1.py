"""Freeze the OpenTTD tool-state program-boundary diagnostic."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/openttd-tool-boundary-01'
SOURCES = ['preregister_openttd_tool_boundary_v1.py', 'probe_openttd_tool_boundary_v1.py',
           'audit_openttd_tool_boundary_v1.py', 'pointer_socket_entry_v8.py', 'durable_submit_v4.py',
           'received_continuation_v1.py', 'received_exchange_v2.py', 'session_v22.py']
TASK = ['openttd_task/interactive_l_v1.py', 'openttd_task/guarded_l_score_v1.py',
        'openttd_task/results/l-geometry-01/baseline.sav']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


ROOT.mkdir(parents=True, exist_ok=False)
plan = {'study': 'openttd-tool-boundary-01', 'status': 'PREREGISTERED_BEFORE_EXECUTION', 'model_calls': 0,
        'modes': [{'mode': 'combined', 'delay_seconds': 0}, {'mode': 'split-immediate', 'delay_seconds': 0},
                  {'mode': 'split-delay-15s', 'delay_seconds': 15}],
        'fixed_effect': 'open road toolbar at 820,51; select first road tool at 709,90; drag 705,240 through 673,256 to 641,272',
        'target_tiles': [977, 978, 979, 1043, 1107],
        'primary_measurement': 'target and surrounding road-owner effects after fresh restore',
        'decision_rule': 'if split modes differ from combined, bind selected tool state across program boundaries; if equal, continue diagnosis elsewhere',
        'scope': 'three scripted episodes; no model judgment, autonomous targeting, human-tempo, token or broad app-state claim',
        'sources': {**{name: sha(HERE / name) for name in SOURCES}, **{name: sha(HERE.parent / name) for name in TASK}}}
temporary = ROOT / 'preregistration.json.tmp'
temporary.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
os.replace(temporary, ROOT / 'preregistration.json')
print(ROOT / 'preregistration.json')
