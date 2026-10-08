"""Freeze the unchanged v9 live-memory replication before execution."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/timing-envelope-openttd-l-10'
PRIOR = HERE / 'results/timing-envelope-openttd-l-09'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    names = [
        'timing_envelope_openttd_l_supervisor_v10.py',
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
        'study': 'timing-envelope-openttd-l-10',
        'replication_of': 'timing-envelope-openttd-l-09',
        'normalization': 'only supervisor self name and study output name differ',
        'arm': 'fixed-astra',
        'task': 'byte-pinned seed991003 five-tile L; same target, forbidden and guard tiles',
        'model_route': 'all gpt-6-astra medium; no automatic retry',
        'max_turns': 12,
        'intervention': 'unchanged one-unresolved-drag bounded effect memory',
        'primary_endpoint': 'independent hard success on the first and only execution',
        'secondary_endpoints': [
            'checkpoint transition sequence',
            'distinct versus repeated drag count',
            'model turns and actual token usage',
            'model wait, proposal-to-feedback and semantic completion',
            'verified input release terminals',
        ],
        'prior_v9': {
            'hard_success': True,
            'model_turns': 9,
            'input_tokens': 151853,
            'semantic_completion_ms': 153026.5392,
            'repeated_completed_segment_drags': 0,
            'audit_sha256': sha(PRIOR / 'audit.json'),
        },
        'decision_rule': 'retain first outcome without retry; do not promote from two live memory episodes',
        'sources': {name: sha(HERE / name) for name in names},
    }
    (OUT / 'preregistration.json').write_text(
        json.dumps(preregistration, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(preregistration, indent=2))


if __name__ == '__main__':
    main()
