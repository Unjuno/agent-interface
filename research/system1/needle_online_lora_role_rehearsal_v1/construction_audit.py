"""Independent, excluded-seed replay of construction seed 735014."""
import json
import sys
from pathlib import Path

import audit
import torch


def main(raw_path, report_path):
    raw_bytes = Path(raw_path).read_bytes()
    payload = json.loads(raw_bytes, object_pairs_hook=audit.unique_pairs)
    row = payload["run"]
    seed = payload["seed"]
    errors = []
    if payload.get("formal") is not False or seed != 735014 or row.get("seed") != seed:
        errors.append("construction_identity")
    core, train_x, train_y, schedule = audit.make_base(seed)
    for parameter in core.parameters():
        parameter.requires_grad_(False)
    base = audit.state_dict_json(core)
    if (row.get("base") != base or row.get("base_sha256") != audit.sha(audit.canonical(base))
            or row.get("base_after_sha256") != audit.sha(audit.canonical(base))
            or row.get("base_immutable") is not True):
        errors.append("base_replay")
    memory = audit.sample(16, seed, 202, 0)
    support = audit.sample(16, seed, 303, 1)
    test_a, test_b = audit.sample(256, seed, 404, 0), audit.sample(256, seed, 505, 1)
    expected = (("base_train_x", train_x.tolist()), ("base_train_y", train_y.tolist()),
                ("base_row_indices", schedule), ("memory_x", memory.tolist()),
                ("memory_y", audit.a_labels(memory).tolist()), ("support_x", support.tolist()),
                ("support_y", audit.b_labels(support).tolist()), ("test_a_x", test_a.tolist()),
                ("test_a_y", audit.a_labels(test_a).tolist()), ("test_b_x", test_b.tolist()),
                ("test_b_y", audit.b_labels(test_b).tolist()))
    for key, value in expected:
        if row.get(key) != value:
            errors.append("data:" + key)
    areas = [{tuple(vector) for vector in x} for x in
             (train_x.tolist(), memory.tolist(), support.tolist(), test_a.tolist(), test_b.tolist())]
    if any(areas[i] & areas[j] for i in range(5) for j in range(i + 1, 5)):
        errors.append("cross_split_overlap")
    torch.manual_seed(seed + 500)
    init = {"left": (torch.randn(16, 2) * 0.1).tolist(), "right": torch.zeros(2, 4).tolist()}
    if row.get("init_adapter") != init:
        errors.append("adapter_init")
    arm_map = {item.get("arm"): item for item in row.get("arms", [])}
    if set(arm_map) != set(audit.ARMS):
        errors.append("arm_denominator")
    accuracies = {}
    for arm in audit.ARMS:
        audit.CURRENT_ARM[arm] = arm_map[arm]
        arm_errors, curves, max_ms = audit.replay_arm(seed, arm, core, support, audit.b_labels(support),
                                                       memory, audit.a_labels(memory), test_a, test_b, init)
        errors.extend(arm_errors)
        accuracies[arm] = {"A": curves["A"], "B": curves["B"], "max_update_ms": max_ms}
    result = {"audit": "PASS_CONSTRUCTION_AUDIT" if not errors else "FAIL_CONSTRUCTION_AUDIT",
              "formal": False, "seed": seed, "errors": errors,
              "raw_bytes": len(raw_bytes), "raw_sha256": audit.sha(raw_bytes), "arms": accuracies}
    with Path(report_path).open("xb") as output:
        output.write(audit.canonical(result) + b"\n")
    print(json.dumps({"audit": result["audit"], "formal": False, "errors": len(errors),
                      "raw_sha256": result["raw_sha256"]}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: construction_audit.py RAW_JSON REPORT_JSON")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
