"""Allocation-v2 independent audit wrapper; delegates calculations to frozen v1 auditor."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ALLOCATION = "needle-lora-rank1-online-skill-v2"
ISSUE = 4507
SEEDS = (74111, 74222, 74333)

dependency = Path("/src/v1")
if not dependency.is_dir():
    dependency = Path(__file__).resolve().parent.parent / "needle_lora_rank1_online_skill_v1"
sys.path.insert(0, str(dependency))
import audit as frozen_auditor

frozen_auditor.ALLOCATION = ALLOCATION
frozen_auditor.SEEDS = SEEDS


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def nearest_rank(values, q):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)] if ordered else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--dependency", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    source, dependency_path, output = Path(args.source), Path(args.dependency), Path(args.out)
    freeze = json.loads((source / "FREEZE.json").read_text(encoding="utf-8"))
    errors = []
    freeze_sha = digest(source / "FREEZE.json")
    if (source / "FREEZE.sha256").read_text(encoding="ascii").strip() != freeze_sha:
        errors.append("freeze_sidecar")
    for relative, expected in freeze["source_sha256"].items():
        if digest(source / relative) != expected:
            errors.append("source_hash:" + relative)
    for relative, expected in freeze["dependency_sha256"].items():
        if digest(dependency_path / relative) != expected:
            errors.append("dependency_hash:" + relative)

    invocation = json.loads((output / "FORMAL_INVOCATION.json").read_text(encoding="utf-8"))
    if (invocation.get("allocation") != ALLOCATION or invocation.get("issue") != ISSUE
            or invocation.get("formal_invocations") != 1 or invocation.get("retry_count") != 0
            or invocation.get("freeze_sha256") != freeze_sha):
        errors.append("invocation_contract")
    run_dir = output / "training"
    run = json.loads((run_dir / "RUN.json").read_text(encoding="utf-8"))
    if (run.get("allocation") != ALLOCATION or run.get("formal_invocations") != 1
            or run.get("retry_count") != 0 or run.get("seeds") != list(SEEDS)):
        errors.append("run_contract")

    per_seed, times = {}, {"1": [], "2": []}
    for seed in SEEDS:
        filename = f"seed-{seed}.json"
        if run.get("result_sha256", {}).get(filename) != digest(run_dir / filename):
            errors.append("result_hash:" + filename)
        row, curves, role_a, seed_errors = frozen_auditor.audit_seed(run_dir / filename, seed)
        errors.extend(f"{seed}:{problem}" for problem in seed_errors)
        for rank in ("1", "2"):
            times[str(rank)].extend(curves[str(rank)]["update_ms"])
        per_seed[str(seed)] = {
            "role_a_accuracy": role_a,
            "rank1_final_accuracy": curves["1"]["accuracy"][-1],
            "rank2_final_accuracy": curves["2"]["accuracy"][-1],
            "rank1_accuracy_curve": curves["1"]["accuracy"],
            "rank2_accuracy_curve": curves["2"]["accuracy"],
            "rank1_update_p95_ms": nearest_rank(curves["1"]["update_ms"], .95),
            "rank2_update_p95_ms": nearest_rank(curves["2"]["update_ms"], .95),
        }
    rank1 = [item["rank1_final_accuracy"] for item in per_seed.values()]
    rank2 = [item["rank2_final_accuracy"] for item in per_seed.values()]
    role_a = [item["role_a_accuracy"] for item in per_seed.values()]
    rank1_p95, rank2_p95 = nearest_rank(times["1"], .95), nearest_rank(times["2"], .95)
    if errors:
        decision = "HOLD_AUDIT_INTEGRITY"
    elif min(rank1) < .90 or min(role_a) < .90 or any(a < b - .03 for a, b in zip(rank1, rank2)):
        decision = "FAIL_RANK1_SKILL_CAPACITY"
    elif rank1_p95 > 60 or rank2_p95 <= 0 or rank1_p95 > .80 * rank2_p95:
        decision = "HOLD_NO_REALTIME_BENEFIT"
    else:
        decision = "PASS_RANK1_ONLINE_SKILL_SCOPED"
    report = {
        "schema": "needle-rank1-online-audit-v2.v1", "allocation": ALLOCATION, "issue": ISSUE,
        "audit": "PASS_AUDIT" if not errors else "FAIL_AUDIT", "decision": decision,
        "errors": errors, "freeze_sha256": freeze_sha,
        "source_sha256": freeze["source_sha256"], "dependency_sha256": freeze["dependency_sha256"],
        "docker_image_id": freeze["docker_image_id"], "seeds": per_seed,
        "aggregate": {"rank1_update_n": len(times["1"]), "rank2_update_n": len(times["2"]),
                      "rank1_update_p50_ms": nearest_rank(times["1"], .50),
                      "rank1_update_p95_ms": rank1_p95, "rank2_update_p95_ms": rank2_p95,
                      "rank1_to_rank2_p95_ratio": rank1_p95 / rank2_p95 if rank1_p95 is not None and rank2_p95 else None},
        "thresholds": {"accuracy_min": .90, "max_loss_vs_rank2": .03,
                       "rank1_p95_ms_max": 60, "rank1_to_rank2_p95_ratio_max": .80},
    }
    with (output / "AUDIT.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
        handle.write("\n")
    print(json.dumps({"audit": report["audit"], "decision": decision, "errors": len(errors),
                      "rank1_p95_ms": rank1_p95, "rank2_p95_ms": rank2_p95}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
