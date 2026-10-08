"""Raw-result auditor with a separately hand-classified finite oracle table."""

import json
import sys


EXPECTED = {
    "same_rack_same_site_distinct_hosts": ("SUSPECTED_UNAVAILABLE", 1, 2),
    "different_racks_same_site": ("SUSPECTED_UNAVAILABLE", 1, 2),
    "different_sites": ("FAILED", 2, 2),
    "stale_generation_second_site": ("SUSPECTED_UNAVAILABLE", 1, 1),
    "one_observer_two_site_claims": ("SUSPECTED_UNAVAILABLE", 1, 1),
}


def audit_results(results):
    errors = []
    observed = set()
    for row in results:
        case_id = row.get("case_id") if isinstance(row, dict) else None
        if case_id not in EXPECTED:
            errors.append(f"unknown or malformed case: {case_id!r}")
            continue
        if case_id in observed:
            errors.append(f"duplicate case: {case_id}")
            continue
        observed.add(case_id)
        expected_state, expected_domains, expected_witnesses = EXPECTED[case_id]
        if row.get("state") != expected_state:
            errors.append(f"{case_id}: state {row.get('state')!r} != {expected_state!r}")
        if row.get("independent_domain_count") != expected_domains:
            errors.append(f"{case_id}: independent-domain count mismatch")
        if row.get("valid_witness_count") != expected_witnesses:
            errors.append(f"{case_id}: valid-witness count mismatch")
    missing = set(EXPECTED) - observed
    errors.extend(f"missing case: {case_id}" for case_id in sorted(missing))
    return errors


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as stream:
        payload = json.load(stream)
    errors = audit_results(payload.get("results", []))
    print(json.dumps({"audit": "FAIL" if errors else "PASS", "errors": errors}, indent=2, sort_keys=True))
    raise SystemExit(bool(errors))
