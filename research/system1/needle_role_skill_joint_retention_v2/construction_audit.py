"""Independent audit of the excluded construction seed."""
import json
import sys
from pathlib import Path

import audit
import torch


def main(raw_path, report_path):
    raw_bytes = Path(raw_path).read_bytes()
    payload = json.loads(raw_bytes, object_pairs_hook=audit.unique_pairs)
    run, seed = payload["run"], payload["seed"]
    errors = []
    if payload.get("formal") is not False or seed != 736514 or run.get("seed") != seed:
        errors.append("construction_identity")
    core, train_x, train_y, schedule = audit.make_base(seed)
    for parameter in core.parameters():
        parameter.requires_grad_(False)
    base = audit.state_dict_json(core)
    if (run.get("base") != base or run.get("base_sha256") != audit.sha(audit.canonical(base))
            or run.get("base_after_sha256") != audit.sha(audit.canonical(base))
            or run.get("base_immutable") is not True):
        errors.append("base_replay")
    memory, support = audit.sample(16, seed, 202, 0), audit.sample(16, seed, 303, 1)
    test_a, test_b = audit.sample(256, seed, 404, 0), audit.sample(256, seed, 505, 1)
    fields = (("base_train_x", train_x.tolist()), ("base_train_y", train_y.tolist()),
              ("base_row_indices", schedule), ("memory_x", memory.tolist()),
              ("memory_y", audit.a_labels(memory).tolist()), ("support_x", support.tolist()),
              ("support_y", audit.b_labels(support).tolist()), ("test_a_x", test_a.tolist()),
              ("test_a_y", audit.a_labels(test_a).tolist()), ("test_b_x", test_b.tolist()),
              ("test_b_y", audit.b_labels(test_b).tolist()))
    expected_hash_keys = {key for key, _ in fields}
    if set(run.get("dataset_sha256", {})) != expected_hash_keys:
        errors.append("dataset_hash_key_set")
    for key, value in fields:
        if run.get(key) != value:
            errors.append("data:" + key)
        if run.get("dataset_sha256", {}).get(key) != audit.sha(audit.canonical(value)):
            errors.append("digest:" + key)
    areas = [{tuple(row) for row in x.tolist()} for x in (train_x, memory, support, test_a, test_b)]
    if any(areas[i] & areas[j] for i in range(5) for j in range(i + 1, 5)):
        errors.append("split_overlap")
    torch.manual_seed(seed + 500)
    init = {"left": (torch.randn(16, 2) * 0.1).tolist(), "right": torch.zeros(2, 4).tolist()}
    if run.get("init_adapter") != init:
        errors.append("initial_adapter")
    arm_map = {item.get("arm"): item for item in run.get("arms", [])}
    if set(arm_map) != set(audit.ARMS):
        errors.append("arm_denominator")
    results = {}
    for arm in audit.ARMS:
        arm_errors, curves, maximum = audit.replay_arm(arm, core, support, audit.b_labels(support), memory,
                                                       audit.a_labels(memory), test_a, test_b, init, arm_map[arm])
        errors.extend(arm_errors)
        results[arm] = {"A": curves["A"][-1], "B": curves["B"][-1], "max_update_ms": maximum}
    result = {"audit": "PASS_CONSTRUCTION_AUDIT" if not errors else "FAIL_CONSTRUCTION_AUDIT",
              "formal": False, "seed": seed, "errors": errors, "raw_bytes": len(raw_bytes),
              "raw_sha256": audit.sha(raw_bytes), "final": results}
    Path(report_path).write_bytes(audit.canonical(result) + b"\n")
    print(json.dumps({"audit": result["audit"], "errors": len(errors),
                      "raw_sha256": result["raw_sha256"]}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: construction_audit.py RAW_JSON REPORT_JSON")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))

