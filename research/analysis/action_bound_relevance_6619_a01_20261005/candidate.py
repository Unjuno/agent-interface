"""One-shot comparison; scorer-only oracle is not read by this program."""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASELINE_PATH = HERE / 'sources' / 'observation_relevance_completeness_1726_candidate.py'
spec = importlib.util.spec_from_file_location('o3_complete_baseline', BASELINE_PATH)
BASELINE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BASELINE)


def delta(case):
    a, b = case['before'], case['current']
    if type(a) is not str or type(b) is not str or len(a) != len(b):
        return None
    return [i for i, (x, y) in enumerate(zip(a, b)) if x != y]


def valid_receipt(case):
    r, p = case['receipt'], case['prediction']
    return (r.get('acknowledged') is True
            and r.get('action_id') == p.get('action_id')
            and r.get('source_epoch') == p.get('source_epoch')
            and r.get('viewport_generation') == p.get('viewport_generation'))


def run_case(case):
    changed = delta(case)
    changed_set = set(changed or [])
    valid = valid_receipt(case)
    p = case['prediction']
    matched = (changed is not None and p.get('uncertainty_pixels') == 0
               and changed == p.get('expected_changed_pixels'))
    declared = set(case['contract'].get('required_pixels', []))
    critical = set(case['contract'].get('critical_pixels', []))
    current_delta = changed or []
    full = current_delta
    prediction_only = [] if valid and matched else full
    # Exact frozen #1726 function; an unbound/stale receipt fails open.
    relevance_decision = BASELINE.complete_only(
        declared, critical, changed_set,
        case['contract'].get('coverage', 'UNKNOWN'), current=valid)
    complete = [] if relevance_decision == 'SUPPRESS' else full
    return {'id': case['id'], 'changed_pixels': changed,
            'receipt_valid': valid, 'prediction_matches': matched,
            'origin_claim': 'UNATTRIBUTED',
            'full_frame': {'decision': 'FORWARD' if full else 'NO_CHANGE',
                           'forwarded_pixels': full, 'delivery_tick': case['decision_tick']},
            'prediction_only': {'decision': 'SUPPRESS' if not prediction_only and full else 'FORWARD' if prediction_only else 'NO_CHANGE',
                                'forwarded_pixels': prediction_only, 'delivery_tick': case['decision_tick']},
            'complete_relevance': {'decision': relevance_decision,
                                   'forwarded_pixels': complete, 'delivery_tick': case['decision_tick']}}


def main():
    if len(sys.argv) != 3:
        raise SystemExit('usage: candidate.py PUBLIC_CASES OUTPUT_RAW')
    src, out = map(Path, sys.argv[1:])
    if out.exists():
        raise SystemExit(f'refusing to overwrite retained output: {out}')
    doc = json.loads(src.read_text())
    raw = {'schema': 'action-bound-relevance-candidate-raw-v1',
           'results': [run_case(case) for case in doc['cases']]}
    out.write_text(json.dumps(raw, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'row_count': len(raw['results']), 'output': str(out)}, sort_keys=True))


if __name__ == '__main__':
    main()
