"""Freeze an ABBA fixed-image targeting comparison for opaque versus transparent signs."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/openttd-sign-target-pair-01'
OPAQUE = HERE / 'results/openttd-sign-view-paused-01/run/runtime/005.png'
TRANSPARENT = HERE / 'results/openttd-sign-view-paused-01/run/runtime/008.png'
SOURCES = ['preregister_openttd_sign_target_pair_v1.py', 'run_openttd_sign_target_pair_v1.py',
           'audit_openttd_sign_target_pair_v1.py', 'model_pair_runner_v2.py',
           'results/openttd-sign-view-paused-01/audit.json']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


prompt = '''You are choosing the drag endpoints for the next visual action in the shown isolated OpenTTD task. The task is to build a straight road connecting only the three ground tiles from A to C and keep the adjacent X forbidden row clear. Trees are already transparent. Point to the visual centers of the underlying ground tiles A and C where a road drag should start and end. Floating text is an annotation, not the ground surface. Do not use tools and do not describe toolbar actions. Return ONLY one JSON object with exactly these integer fields: {"start_x":0,"start_y":0,"end_x":0,"end_y":0}.''' 
ROOT.mkdir(parents=True, exist_ok=False)
(ROOT / 'prompt.txt').write_text(prompt, encoding='utf-8')
plan = {
    'study': 'openttd-sign-target-pair-01',
    'status': 'PREREGISTERED_BEFORE_MODEL_CALLS',
    'order': ['opaque-sign-background', 'transparent-sign-background',
              'transparent-sign-background', 'opaque-sign-background'],
    'model': 'gpt-6-astra',
    'effort': 'medium',
    'same_prompt_sha256': sha(ROOT / 'prompt.txt'),
    'conditions': {
        'opaque-sign-background': {'image': str(OPAQUE.relative_to(HERE)), 'sha256': sha(OPAQUE)},
        'transparent-sign-background': {'image': str(TRANSPARENT.relative_to(HERE)), 'sha256': sha(TRANSPARENT)},
    },
    'hidden_scoring_reference': {
        'start': [737, 250], 'end': [673, 282],
        'basis': 'previous independently successful seed-991002 live road drag; never included in model prompt',
        'endpoint_gate': 'absolute x error <=12 and absolute y error <=6 for both named endpoints',
    },
    'decision_rule': 'report per-condition 0/2 endpoint-gate passes, coordinates, model time and actual reported tokens; do not promote from one fixed image pair',
    'no_retry': True,
    'sources': {name: sha(HERE / name) for name in SOURCES},
    'scope': 'fixed-image grounding diagnostic; no GUI execution, task success, causal speed or broad token claim',
}
temporary = ROOT / 'preregistration.json.tmp'
temporary.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
os.replace(temporary, ROOT / 'preregistration.json')
print(ROOT / 'preregistration.json')
