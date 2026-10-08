"""Freeze a two-context archived-image decision probe before model execution."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
FROZEN = HERE / 'results/timing-envelope-openttd-l-08/fixed-astra'
MEMORY = HERE / 'results/openttd-effect-memory-v1'
OUT = HERE / 'results/openttd-effect-memory-decisions-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    cases = []
    for turn in (7, 8):
        cases.append({
            'turn': turn,
            'prompt': str(FROZEN / f'prompt-{turn}.txt'),
            'prompt_sha256': sha(FROZEN / f'prompt-{turn}.txt'),
            'baseline_image': str(FROZEN / f'planner-{turn}.png'),
            'baseline_image_sha256': sha(FROZEN / f'planner-{turn}.png'),
            'baseline_typed': str(FROZEN / f'typed-{turn}.json'),
            'baseline_typed_sha256': sha(FROZEN / f'typed-{turn}.json'),
            'memory_image': str(MEMORY / f'replayed-planner-{turn}.png'),
            'memory_image_sha256': sha(MEMORY / f'replayed-planner-{turn}.png'),
            'output': str(OUT / f'memory-turn{turn}'),
        })
    preregistration = {
        'status': 'preregistered_before_model_execution',
        'design': 'two retained v8 contexts; exact original prompt; baseline raw output versus one new memory-image call per context',
        'model_route': {'model': 'gpt-6-astra', 'effort': 'medium'},
        'cases': cases,
        'required_checkpoint_prior_turn': 5,
        'primary_endpoint': 'checkpoint status distribution: observed, uncertain or contradicted',
        'secondary_endpoints': [
            'schema-valid proposal count',
            'proposal kind and intent',
            'input/cached/output tokens',
        ],
        'interpretation': 'descriptive fixed-context signal only; separate model samples prevent a causal claim',
        'promotion_gate': 'do not promote from this probe; require a fresh preregistered live episode and independent engine score',
        'sources': {
            'effect_memory': sha(HERE / 'openttd_effect_memory_v1.py'),
            'memory_audit': sha(HERE / 'audit_openttd_effect_memory_v1.py'),
            'model_runner': sha(HERE / 'model_pair_runner_v2.py'),
            'checkpoint_parser': sha(HERE / 'semantic_checkpoint_v4.py'),
        },
    }
    (OUT / 'preregistration.json').write_text(
        json.dumps(preregistration, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(preregistration, indent=2))


if __name__ == '__main__':
    main()
