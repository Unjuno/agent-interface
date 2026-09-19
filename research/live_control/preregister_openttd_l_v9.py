"""Freeze the first live bounded-effect-memory allocation before execution."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/timing-envelope-openttd-l-09'
PRIOR = HERE / 'results/timing-envelope-openttd-l-08'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    sources = [
        'timing_envelope_openttd_l_supervisor_v9.py',
        'timing_envelope_openttd_l_supervisor_v8.py',
        'timing_envelope_openttd_l_driver_v6.py',
        'openttd_effect_memory_v1.py',
        'semantic_checkpoint_v4.py',
        'openttd_finish_outcome_v2.py',
        'model_pair_runner_v2.py',
        'session_v22.py',
    ]
    preregistration = {
        'status': 'preregistered_before_execution',
        'study': 'timing-envelope-openttd-l-09',
        'arm': 'fixed-astra',
        'task': 'byte-pinned seed991003 five-tile L; same target, forbidden and guard tiles as v7/v8',
        'model_route': 'all gpt-6-astra medium; no automatic retry',
        'max_turns': 12,
        'intervention': 'retain exactly one unresolved drag as original before/after, latest inspection and action difference',
        'unchanged_gates': [
            'uncertain checkpoint permits observation-only inspection',
            'new progress mutation requires observed prior effect',
            'independent engine score is authoritative',
            'all runtime terminals require released input',
        ],
        'primary_endpoint': 'independent hard success on the first execution',
        'secondary_endpoints': [
            'repeated completed A-to-B drag count',
            'model turns and actual token usage',
            'proposal-to-first-useful-feedback and model wait',
            'effect-memory source turn and inspection count',
            'typed controller finish reason',
        ],
        'prior_v8': {
            'hard_success': False,
            'model_turns': 8,
            'input_tokens': 133041,
            'semantic_outcome': 'typed_model_safe_stop',
            'repeated_A_to_B_drags': 0,
            'audit_sha256': sha(PRIOR / 'audit.json'),
        },
        'decision_rule': 'retain as live evidence regardless of outcome; no promotion from one episode',
        'sources': {name: sha(HERE / name) for name in sources},
    }
    (OUT / 'preregistration.json').write_text(
        json.dumps(preregistration, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(preregistration, indent=2))


if __name__ == '__main__':
    main()
