from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DOOM = REPO / 'research' / 'doom'
ANALYZER = DOOM / 'analyze_map01_held_input_occupancy_v1.py'
EXPECTED = {
    'map01-v38-integrated-threat-live-01': {
        'report.json': '7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58',
        'runtime/events.jsonl': '80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3',
    },
    'map01-v39-coast-liveness-live-01': {
        'report.json': '719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687',
        'runtime/events.jsonl': '2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381',
    },
}
MAX_WIDTH_TO_MODEL_WAIT = 0.10
MAX_WIDTH_TO_OCCUPANCY_UPPER = 0.25

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_analyzer():
    spec = importlib.util.spec_from_file_location('held_occ_frozen', ANALYZER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    held = load_analyzer()
    runs = []
    for name, expected in EXPECTED.items():
        root = DOOM / 'results' / name
        actual = {
            'report.json': sha256(root / 'report.json'),
            'runtime/events.jsonl': sha256(root / 'runtime/events.jsonl'),
        }
        if actual != expected:
            raise RuntimeError(f'source hash mismatch for {name}: {actual} != {expected}')
        value = held.analyze(root)
        if value['source_sha256'] != expected:
            raise RuntimeError(f'analyzer source binding mismatch for {name}')
        total_wait = round(sum(row['model_wait_ms'] for row in value['decisions']), 3)
        lower = value['totals']['physical_any_key_occupancy_lower_ms']
        upper = value['totals']['physical_any_key_occupancy_upper_ms']
        width = value['totals']['occupancy_interval_width_ms']
        width_to_wait = (width / total_wait) if total_wait else None
        width_to_upper = (width / upper) if upper else 0.0
        informative = (width_to_wait is not None and width_to_wait <= MAX_WIDTH_TO_MODEL_WAIT
                       and width_to_upper <= MAX_WIDTH_TO_OCCUPANCY_UPPER)
        runs.append({
            **value,
            'total_model_wait_ms': total_wait,
            'diagnostic': {
                'width_to_model_wait': width_to_wait,
                'width_to_occupancy_upper': width_to_upper,
                'max_width_to_model_wait': MAX_WIDTH_TO_MODEL_WAIT,
                'max_width_to_occupancy_upper': MAX_WIDTH_TO_OCCUPANCY_UPPER,
                'informative_enough_for_next_matched_metric': informative,
            },
        })
    decision = ('RETAIN_FULL_OCCUPANCY_INTERVALS_SCOPED'
                if all(r['diagnostic']['informative_enough_for_next_matched_metric'] for r in runs)
                else 'SCHEMA_CENSORING_TOO_WIDE')
    result = {
        'schema': 'map01-held-input-occupancy-full-posthoc-v1',
        'task': 'MAP01-HELD-OCCUPANCY-FULL-POSTHOC-20260916-001',
        'analysis_kind': 'retained-log posthoc; no live/model/input execution',
        'existing_analyzer_git_blob': '4ac4180f8768b3c94f2da5d0e0abcf20de2d69ca',
        'existing_test_git_blob': '6fd9713dbcfc449296d6dcba0b63062ea32bb28a',
        'decision': decision,
        'runs': runs,
        'limits': [
            'exact normal key-up time remains unobserved',
            'occupancy is physical any-key actuation, not independently verified useful control',
            'v38/v39 are stochastic retained episodes and are not a causal matched comparison',
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({
        'decision': decision,
        'runs': [{
            'run': r['run'],
            'hold_steps': r['totals']['hold_steps'],
            'model_wait_ms': r['total_model_wait_ms'],
            'occupancy_lower_ms': r['totals']['physical_any_key_occupancy_lower_ms'],
            'occupancy_upper_ms': r['totals']['physical_any_key_occupancy_upper_ms'],
            'interval_width_ms': r['totals']['occupancy_interval_width_ms'],
            **r['diagnostic'],
        } for r in runs],
    }, indent=2))

if __name__ == '__main__':
    main()
