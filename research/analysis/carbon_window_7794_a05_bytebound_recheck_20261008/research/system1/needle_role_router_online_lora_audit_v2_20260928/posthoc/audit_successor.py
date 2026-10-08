"""Post-hoc raw-only audit of Issue #4899 with an explicit schedule contract.

The predecessor audit implementation is used only for deterministic model and
trajectory reconstruction. This successor separately validates the actual raw
schema and treats base_row_indices as a reconstructed schedule, not as a member
of the producer's dataset_sha256 map. It never invokes the trainer.
"""
import hashlib
import json
import sys
from pathlib import Path

import torch

import audit as predecessor

EXPECTED_RAW_SHA256 = "7ff93c67a4bc8e9f864511f1b89bf4fe2109287fd359927fee51de345c10188b"
EXPECTED_RAW_BYTES = 1_611_168
DATA_FIELDS = (
    "base_train_x", "base_train_y", "memory_x", "memory_y", "support_x",
    "support_y", "test_a_x", "test_a_y", "test_b_x", "test_b_y",
)
DECLARED_SCHEDULE = "base_row_indices"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def expected_schedule(seed):
    generator = torch.Generator().manual_seed(seed + 102)
    return torch.randint(256, (400,), generator=generator).tolist()


def validate_run_raw(run_row, seed):
    errors = []
    if run_row.get("seed") != seed:
        return [f"{seed}:seed_identity"]
    schedule = run_row.get(DECLARED_SCHEDULE)
    if schedule != expected_schedule(seed):
        errors.append(f"{seed}:schedule_reconstruction")
    digests = run_row.get("dataset_sha256")
    if not isinstance(digests, dict) or set(digests) != set(DATA_FIELDS):
        errors.append(f"{seed}:dataset_digest_field_set")
        return errors
    for field in DATA_FIELDS:
        value = run_row.get(field)
        if value is None or digests.get(field) != sha(canonical(value)):
            errors.append(f"{seed}:{field}:digest")
    return errors


def audit(raw_path, report_path):
    raw_bytes = Path(raw_path).read_bytes()
    actual_raw_sha = sha(raw_bytes)
    errors, misses, results = [], [], []
    if len(raw_bytes) != EXPECTED_RAW_BYTES or actual_raw_sha != EXPECTED_RAW_SHA256:
        errors.append("source_raw_identity")
    raw = json.loads(raw_bytes, object_pairs_hook=predecessor.unique_pairs)
    if (raw.get("schema") != "needle-role-router-raw-v1"
            or raw.get("allocation") != predecessor.ALLOCATION
            or tuple(raw.get("seeds", ())) != predecessor.SEEDS
            or tuple(raw.get("arms", ())) != predecessor.ARMS):
        errors.append("raw_identity")
    if [row.get("seed") for row in raw.get("runs", [])] != list(predecessor.SEEDS):
        errors.append("seed_denominator")

    for run_row in raw.get("runs", []):
        seed = run_row["seed"]
        errors.extend(validate_run_raw(run_row, seed))

        # Deterministically regenerate the base and all data splits. The schedule
        # is checked by exact values; it is intentionally not required to appear
        # as a dataset digest because the frozen producer's digest contract omits it.
        core, train_x, train_y, schedule = predecessor.make_base(seed)
        for parameter in core.parameters():
            parameter.requires_grad_(False)
        base = predecessor.state_dict_json(core)
        if (run_row.get("base") != base
                or run_row.get("base_sha256") != sha(canonical(base))
                or run_row.get("base_after_sha256") != sha(canonical(base))
                or run_row.get("base_immutable") is not True):
            errors.append(f"{seed}:base_or_immutability")

        memory = predecessor.sample(16, seed, 202, 0)
        support = predecessor.sample(16, seed, 303, 1)
        test_a = predecessor.sample(256, seed, 404, 0)
        test_b = predecessor.sample(256, seed, 505, 1)
        expected = {
            "base_train_x": train_x.tolist(), "base_train_y": train_y.tolist(),
            "memory_x": memory.tolist(),
            "memory_y": predecessor.a_labels(memory).tolist(),
            "support_x": support.tolist(),
            "support_y": predecessor.b_labels(support).tolist(),
            "test_a_x": test_a.tolist(),
            "test_a_y": predecessor.a_labels(test_a).tolist(),
            "test_b_x": test_b.tolist(),
            "test_b_y": predecessor.b_labels(test_b).tolist(),
        }
        if run_row.get(DECLARED_SCHEDULE) != schedule:
            errors.append(f"{seed}:schedule_exact")
        for name, value in expected.items():
            if run_row.get(name) != value:
                errors.append(f"{seed}:{name}:reconstruction")
        splits = [set(map(tuple, rows.tolist()))
                  for rows in (train_x, memory, support, test_a, test_b)]
        if any(splits[i] & splits[j]
               for i in range(len(splits)) for j in range(i + 1, len(splits))):
            errors.append(f"{seed}:split_overlap")

        torch.manual_seed(seed + 500)
        init = {"left": (torch.randn(16, 2) * 0.1).tolist(),
                "right": torch.zeros(2, 4).tolist()}
        if run_row.get("init_adapter") != init:
            errors.append(f"{seed}:init_adapter")
        arm_rows = {item.get("arm"): item for item in run_row.get("arms", [])}
        if set(arm_rows) != set(predecessor.ARMS):
            errors.append(f"{seed}:arm_set")
            continue
        final = {}
        for arm in predecessor.ARMS:
            arm_errors, curves, maximum = predecessor.replay_arm(
                arm, core, support, predecessor.b_labels(support), memory,
                predecessor.a_labels(memory), test_a, test_b, init, arm_rows[arm])
            errors.extend(f"{seed}:{error}" for error in arm_errors)
            final[arm] = {"A": curves["A"][-1], "B": curves["B"][-1],
                          "max_update_ms": maximum}
        routed = final["ROUTED_SEPARATE_SKILLS"]
        if (routed["A"] < .90 or routed["B"] < .90
                or any(routed["A"] < final[name]["A"] + .10
                       for name in predecessor.ARMS[:3])
                or routed["B"] < max(final[name]["B"]
                                     for name in predecessor.ARMS[:3]) - .10):
            misses.append({"seed": seed, "routed": routed, "comparators": final})
        results.append({"seed": seed, "final": final})

    report = {
        "schema": "needle-role-router-posthoc-audit-v1",
        "formal_raw_sha256": actual_raw_sha,
        "formal_raw_bytes": len(raw_bytes),
        "original_disposition_preserved": "HOLD_AUDIT_INTEGRITY",
        "integrity": "PASS_POSTHOC_RAW_RECONSTRUCTION" if not errors else "FAIL_POSTHOC_RAW_RECONSTRUCTION",
        "integrity_errors": errors,
        "scientific_diagnostic": "FAIL_ROUTING_OR_RETENTION" if misses else "NO_PREREGISTERED_QUALITY_MISS",
        "scientific_misses": misses,
        "n_seeds": len(results),
        "n_arm_arrival_rows_reconstructed": sum(
            len(arm.get("arrivals", []))
            for run_row in raw.get("runs", []) for arm in run_row.get("arms", [])),
        "results": results,
        "scope": "Post-hoc audit-only replay of immutable #4899 raw; not a registered rerun and cannot retroactively replace its HOLD.",
    }
    Path(report_path).write_bytes(canonical(report) + b"\n")
    print(json.dumps({key: report[key] for key in (
        "integrity", "scientific_diagnostic", "n_seeds",
        "n_arm_arrival_rows_reconstructed", "integrity_errors")},
        sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit_successor.py FORMAL_RAW_JSON REPORT_JSON")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    result = audit(sys.argv[1], sys.argv[2])
    raise SystemExit(0 if result["integrity"] == "PASS_POSTHOC_RAW_RECONSTRUCTION" else 2)

