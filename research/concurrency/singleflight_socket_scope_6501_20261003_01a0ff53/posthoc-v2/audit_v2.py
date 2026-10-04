"""Additive retained-wire adjudication; frozen v1 and primary raw stay unchanged."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audit as original


def audit(raw, fixtures):
    result = original.audit(raw, fixtures)
    for trial in raw['trials']:
        for event in trial['server_events']:
            decoded = json.loads(bytes.fromhex(event['wire_hex']))
            recorded = event['request' if event['event'] == 'server_received' else 'response']
            # JSON serialization distinguishes true, 1, and 1.0 recursively.
            options = dict(sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
            if json.dumps(decoded, **options) != json.dumps(recorded, **options):
                raise ValueError('typed wire binding: ' + event['event'] + ' ' + event['call_id'])
    return result


def main():
    from controls import mutations
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError('posthoc output already exists')
    raw_bytes = args.raw.read_bytes()
    raw = json.loads(raw_bytes)
    fixtures = json.loads(args.fixtures.read_text())
    try:
        result, errors = audit(raw, fixtures), []
    except ValueError as exc:
        result, errors = None, [str(exc)]
    controls = []
    for name, reason, changed, additional in mutations(raw):
        try:
            before = original.audit(changed, fixtures)
            baseline = dict(accepted=True, status=before['status'], error=None)
        except ValueError as exc:
            baseline = dict(accepted=False, status=None, error=str(exc))
        try:
            audit(changed, fixtures)
            fixed_error = None
        except ValueError as exc:
            fixed_error = str(exc)
        controls.append(dict(name=name, additional=additional, required_reason=reason,
                             original_disposition=baseline, corrected_error=fixed_error,
                             rejected_for_required_reason=fixed_error is not None and reason in fixed_error,
                             expected_original_acceptance=additional))
    passed = not errors and all(c['rejected_for_required_reason'] and
                                 c['original_disposition']['accepted'] == c['expected_original_acceptance']
                                 for c in controls)
    record = dict(schema='socket-scope-posthoc-wire-v2',
                  status='PASS_POSTHOC_WIRE_BINDING_SCOPED' if passed else 'FAIL_POSTHOC_WIRE_BINDING',
                  original_primary_outcome_preserved=True, candidate_replay=False,
                  raw_sha256=hashlib.sha256(raw_bytes).hexdigest(), errors=errors,
                  corrected_retained_result=result, wire_events=sum(len(t['server_events']) for t in raw['trials']),
                  controls=controls)
    with args.output.open('x') as out:
        json.dump(record, out, indent=2, sort_keys=True); out.write('\n')
    print(json.dumps(dict(status=record['status'], errors=errors, wire_events=record['wire_events'],
                         original_controls=8, additional_controls=6, candidate_replay=False), sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
