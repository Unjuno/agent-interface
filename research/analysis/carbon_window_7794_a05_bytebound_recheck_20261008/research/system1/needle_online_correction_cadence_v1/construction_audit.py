"""Separate-process, non-formal full raw replay for construction seed 734014."""
import hashlib
import json
import sys
from pathlib import Path

import audit
import torch


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique)


def run(raw_path, output_path):
    raw = load(raw_path)
    run = raw["run"]
    seed = raw["seed"]
    errors = []
    if seed != 734014 or run.get("seed") != seed or run.get("base_immutable") is not True:
        errors.append("allocation_or_base_immutability")
    core, train_x, train_y, indices = audit.regenerate_base(seed)
    for parameter in core.parameters():
        parameter.requires_grad_(False)
    base = audit.tensor_json(core)
    if (run.get("base_train_x") != train_x.tolist() or run.get("base_train_y") != train_y.tolist()
            or run.get("base_row_indices") != indices or run.get("base") != base
            or run.get("base_sha256") != audit.sha(audit.canonical(base))
            or run.get("base_after_sha256") != audit.sha(audit.canonical(base))):
        errors.append("base_training_replay")
    support, support_y = audit.regenerate_support(seed)
    test_a, test_b = audit.sample(256, seed, 303), audit.sample(256, seed, 404)
    if (run.get("support_x") != support.tolist() or run.get("support_y") != support_y.tolist()
            or run.get("test_a_x") != test_a.tolist() or run.get("test_b_x") != test_b.tolist()
            or run.get("test_a_y") != audit.a_labels(test_a).tolist()
            or run.get("test_b_y") != audit.b_labels(test_b).tolist()):
        errors.append("data_or_label_replay")
    split_rows = [{tuple(row) for row in values.tolist()}
                  for values in (train_x, support, test_a, test_b)]
    if any(split_rows[i] & split_rows[j] for i in range(4) for j in range(i + 1, 4)):
        errors.append("cross_split_overlap")
    initial = audit.regenerated_init(seed)
    if run.get("init_adapter") != initial:
        errors.append("adapter_initialization")
    arms = {arm["arm"]: arm for arm in run.get("arms", [])}
    if set(arms) != set(audit.ARMS):
        errors.append("arm_denominator")
    results = {}
    for arm in audit.ARMS:
        arm_errors, accuracy = audit.audit_arm(core, seed, arm, arms[arm], initial,
                                                 support, support_y, test_a, test_b)
        errors.extend(arm_errors)
        results[arm] = {"steps": arms[arm]["optimizer_steps"],
                        "final_A_accuracy": accuracy["A"][-1],
                        "final_B_accuracy": accuracy["B"][-1],
                        "A_curve": accuracy["A"], "B_curve": accuracy["B"],
                        "max_update_ms": max(arms[arm]["update_ns"]) / 1_000_000,
                        "max_burst_ms": max(arms[arm]["burst_ns"]) / 1_000_000}
    expected_controls = [
        {"status": "YIELD", "selected_role": None, "proposal": None},
        {"status": "YIELD", "selected_role": None, "proposal": None},
    ]
    if run.get("invalid_controls") != expected_controls:
        errors.append("route_controls")
    result = {"audit": "PASS_CONSTRUCTION_AUDIT" if not errors else "FAIL_CONSTRUCTION_AUDIT",
              "formal": False, "seed": seed, "errors": errors, "arms": results,
              "raw_sha256": hashlib.sha256(Path(raw_path).read_bytes()).hexdigest()}
    encoded = audit.canonical(result) + b"\n"
    with Path(output_path).open("xb") as f:
        f.write(encoded)
    print(json.dumps({"audit": result["audit"], "errors": len(errors),
                      "raw_sha256": result["raw_sha256"]}, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: construction_audit.py RAW_JSON AUDIT_JSON")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    result = run(sys.argv[1], sys.argv[2])
    raise SystemExit(0 if result["audit"] == "PASS_CONSTRUCTION_AUDIT" else 2)
