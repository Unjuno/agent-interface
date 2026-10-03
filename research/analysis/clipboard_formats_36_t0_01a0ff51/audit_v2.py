"""Additive posthoc raw auditor; the frozen v1 and formal packet stay unchanged."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import audit as v1


def verify(packet, oracle, root):
    errors, findings = v1.verify(packet, oracle, root)
    for row in packet.get('rows', []):
        # These records contain JSON values only. Canonical serialization keeps
        # bool/int/float distinct throughout nested delivered planner metadata.
        if json.dumps(row.get('planner_metadata'), sort_keys=True) != json.dumps(row.get('observed'), sort_keys=True):
            errors.append(row.get('id', '?') + ':planner_scalar_type')
    return errors, findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--oracle', type=Path, required=True)
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError('posthoc output already exists')
    packet, oracle = json.loads(args.raw.read_text()), json.loads(args.oracle.read_text())
    errors, findings = verify(packet, oracle, args.raw.parent)
    controls = v1.mutations(packet, oracle, args.raw.parent)
    additional = []
    for value in (True, 1.0):
        changed = copy.deepcopy(packet)
        changed['rows'][0]['planner_metadata']['generation'] = value
        original_errors, _ = v1.verify(changed, oracle, args.raw.parent)
        fixed_errors, _ = verify(changed, oracle, args.raw.parent)
        additional.append({'mutation': 'planner_generation_to_' + type(value).__name__, 'v1_errors': original_errors, 'v2_errors': fixed_errors, 'rejected_for_required_reason': 'C01:planner_scalar_type' in fixed_errors})
    passed = not errors and all(c['rejected'] for c in controls) and all(c['rejected_for_required_reason'] for c in additional)
    result = {'schema': 'clipboard36-posthoc-audit-v2', 'status': 'PASS_POSTHOC_AUDIT_SCOPED' if passed else 'FAIL_POSTHOC_AUDIT', 'original_formal_outcome_preserved': True, 'candidate_rerun': False, 'raw_sha256': hashlib.sha256(args.raw.read_bytes()).hexdigest(), 'errors': errors, 'findings': findings, 'original_controls': controls, 'additional_scalar_controls': additional}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'errors': errors, 'original_controls': len(controls), 'additional_controls': len(additional), 'candidate_rerun': False}))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
