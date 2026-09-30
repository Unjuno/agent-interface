"""Independent raw-only oracle v1; preserved exactly after its first run."""

import itertools
import json
import sys


def oracle_matrix():
    leaves = list(itertools.product(range(2), repeat=3))
    common_prefix_histogram = {0: 0, 1: 0, 2: 0, 3: 0}
    for left in leaves:
        for right in leaves:
            prefix = 0
            for a, b in zip(left, right):
                if a != b:
                    break
                prefix += 1
            common_prefix_histogram[prefix] += 1

    rows = []
    for configured_cut in (1, 2, 3):
        for latent_boundary in (1, 2, 3):
            false_failed = sum(
                count for prefix, count in common_prefix_histogram.items()
                if prefix < configured_cut and prefix >= latent_boundary
            )
            missed_failed = sum(
                count for prefix, count in common_prefix_histogram.items()
                if prefix < latent_boundary and prefix >= configured_cut
            )
            rows.append({
                "configured_cut": configured_cut,
                "latent_boundary": latent_boundary,
                "false_failed": false_failed,
                "missed_failed": missed_failed,
            })
    return rows, common_prefix_histogram


def audit(raw):
    errors = []
    semantic = raw.get("semantic") if isinstance(raw, dict) else None
    if not isinstance(semantic, dict):
        return ["missing semantic object"]
    expected_rows, histogram = oracle_matrix()
    if semantic.get("schema") != "issue-5531-t5-cut-sensitivity-v1":
        errors.append("schema mismatch")
    if semantic.get("leaf_count") != 8:
        errors.append("leaf_count mismatch")
    if semantic.get("ordered_pair_count") != 64:
        errors.append("ordered_pair_count mismatch")
    if semantic.get("pair_evaluations") != 576:
        errors.append("pair_evaluations mismatch")
    if semantic.get("matrix") != expected_rows:
        errors.append("matrix differs from independently counted common-prefix oracle")
    if histogram != {0: 32, 1: 16, 2: 8, 3: 8}:
        errors.append("internal leaf-pair histogram sanity failure")
    environment = raw.get("environment", {})
    if environment.get("docker_used") is not False:
        errors.append("environment Docker disclosure mismatch")
    if environment.get("candidate_invocations") != 0:
        errors.append("candidate invocation count mismatch")
    return errors


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as stream:
        raw = json.load(stream)
    errors = audit(raw)
    print(json.dumps({"audit": "PASS" if not errors else "FAIL", "errors": errors}, indent=2))
    raise SystemExit(bool(errors))
