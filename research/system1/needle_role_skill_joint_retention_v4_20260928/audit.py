"""Independent raw-only reconstruction of role-routed online skill adapters."""
import hashlib
import json
import random
import statistics
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

SEEDS = (9944211, 9944311, 9944411)
ARMS = ("SHARED_B_ONLY", "SHARED_A_REPLAY", "ROUTED_SHARED_ADAPTER", "ROUTED_SEPARATE_SKILLS")
ALLOCATION = "needle-role-skill-joint-retention-20260928-v4"
IMAGE = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)


def valid_freeze_sidecar(sidecar, freeze_bytes):
    expected = (sha(freeze_bytes) + "\n").encode("ascii")
    return sidecar == expected and len(sidecar) == 65


def invocation_mounts_valid(argv):
    mounts = [argv[i + 1] for i, part in enumerate(argv[:-1]) if part == "--mount"]
    destinations = [mount.split(",dst=", 1)[1] if ",dst=" in mount else "" for mount in mounts]
    sources = [mount.split(",dst=", 1)[0].removeprefix("type=bind,source=")
               if mount.startswith("type=bind,source=") and ",dst=" in mount else "" for mount in mounts]
    return (len(mounts) == 2 and destinations == ["/src,readonly", "/out"]
            and all(sources) and sources[0] != sources[1]
            and sources[1].replace("\\", "/").endswith("/raw"))


def sample(rows, seed, salt, role):
    source = random.Random(seed * 1009 + salt)
    binary = [0, 1] * (rows // 2)
    source.shuffle(binary)
    return torch.tensor([[float(bit), *[source.random() for _ in range(7)], float(role)]
                         for bit in binary], dtype=torch.float32)


def a_labels(x):
    return x[:, 0].long()


def b_labels(x):
    return 1 - x[:, 0].long()


class AuditCore(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = torch.nn.Linear(9, 16)
        self.head = torch.nn.Linear(16, 4)

    def forward(self, x):
        return self.head(torch.tanh(self.enc(x)))


class AuditAdapter(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.left = torch.nn.Parameter(torch.zeros(16, 2))
        self.right = torch.nn.Parameter(torch.zeros(2, 4))

    def forward(self, core, inputs):
        hidden = torch.tanh(core.enc(inputs))
        return core.head(hidden) + (hidden @ self.left @ self.right) / 2


def make_base(seed):
    torch.manual_seed(seed)
    model = AuditCore()
    inputs = sample(256, seed, 101, 0)
    labels = a_labels(inputs)
    schedule = torch.randint(256, (400,), generator=torch.Generator().manual_seed(seed + 102)).tolist()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.03, weight_decay=1e-4)
    for ix in schedule:
        optimizer.zero_grad(set_to_none=True)
        F.cross_entropy(model(inputs[ix:ix + 1]), labels[ix:ix + 1]).backward()
        optimizer.step()
    return model, inputs, labels, schedule


def state_dict_json(module):
    return {key: value.detach().cpu().tolist() for key, value in module.state_dict().items()}


def optimizer_json(optimizer, adapter):
    output = {}
    for name, parameter in zip(("left", "right"), (adapter.left, adapter.right)):
        item = optimizer.state.get(parameter, {})
        output[name] = {"step": float(item["step"].item()) if "step" in item else 0.0,
                        "exp_avg": item["exp_avg"].tolist() if "exp_avg" in item else None,
                        "exp_avg_sq": item["exp_avg_sq"].tolist() if "exp_avg_sq" in item else None}
    return output


def make_batch(arm, bx, by, ax, ay, mem_ix):
    if arm in ("SHARED_B_ONLY", "ROUTED_SHARED_ADAPTER", "ROUTED_SEPARATE_SKILLS"):
        return bx.reshape(1, -1), by.reshape(1)
    if arm == "SHARED_A_REPLAY":
        return torch.stack((bx, ax[mem_ix])), torch.stack((by, ay[mem_ix]))
    raise ValueError("unknown_arm")


def predictions(core, adapter, inputs):
    with torch.no_grad():
        return adapter(core, inputs).argmax(-1).tolist()


def replay_arm(arm, core, support, support_y, memory, memory_y, test_a, test_b, init, raw_arm):
    shared = arm != "ROUTED_SEPARATE_SKILLS"
    a_adapter, b_adapter = AuditAdapter(), AuditAdapter()
    with torch.no_grad():
        for adapter in (a_adapter, b_adapter):
            adapter.left.copy_(torch.tensor(init["left"], dtype=torch.float32))
            adapter.right.copy_(torch.tensor(init["right"], dtype=torch.float32))
    if shared:
        optimizer = torch.optim.AdamW(a_adapter.parameters(), lr=0.04, weight_decay=1e-4)
        b_adapter = a_adapter
    else:
        optimizer = torch.optim.AdamW(b_adapter.parameters(), lr=0.04, weight_decay=1e-4)
    immutable_a = ({key: value.detach().clone() for key, value in a_adapter.state_dict().items()}
                   if not shared else None)
    errors, curves, routes = [], {"A": [], "B": []}, []
    checkpoints = raw_arm.get("arrivals", [])
    for arrival in range(16):
        for step in range(8):
            index = arrival * 8 + step
            route_record = raw_arm.get("routes", [])[index]
            expected = ({"status": "READY", "selected_role": "B", "adapter_id":
                         ("skill-B-online-v1" if arm == "ROUTED_SEPARATE_SKILLS" else
                          "role-shared-online-v1" if arm == "ROUTED_SHARED_ADAPTER" else "shared-online-v1"),
                         "generation": 3, "proposal": None})
            if route_record != expected:
                errors.append(f"{arm}:{index}:route")
            bx, by = support[arrival], support_y[arrival]
            inputs, labels = make_batch(arm, bx, by, memory, memory_y, index % 16)
            selected = b_adapter if route_record.get("adapter_id") in (
                "skill-B-online-v1", "role-shared-online-v1", "shared-online-v1") else None
            if selected is None:
                errors.append(f"{arm}:{index}:invalid_route_mutation_block")
                continue
            optimizer.zero_grad(set_to_none=True)
            F.cross_entropy(selected(core, inputs), labels).backward()
            optimizer.step()
            routes.append(route_record)
        controls = raw_arm.get("yield_controls", [])[arrival]
        invalid = [
            {"status": "YIELD", "selected_role": None, "adapter_id": None, "generation": 3, "proposal": None},
            {"status": "YIELD", "selected_role": None, "adapter_id": None, "generation": 2, "proposal": None},
            {"status": "YIELD", "selected_role": None, "adapter_id": None, "generation": 3, "proposal": None}]
        if controls != invalid:
            errors.append(f"{arm}:{arrival}:yield_controls")
        role_routes = checkpoints[arrival].get("role_routes", [])
        if arm.startswith("ROUTED_"):
            expected_routes = [
                {"status": "READY", "selected_role": "A", "adapter_id":
                 "skill-A-immutable-v1" if not shared else "role-shared-online-v1",
                 "generation": 3, "proposal": None},
                {"status": "READY", "selected_role": "B", "adapter_id":
                 "skill-B-online-v1" if not shared else "role-shared-online-v1",
                 "generation": 3, "proposal": None}]
            if role_routes != expected_routes:
                errors.append(f"{arm}:{arrival}:role_routes")
        elif role_routes:
            errors.append(f"{arm}:{arrival}:unexpected_role_routes")
        if (immutable_a is not None and
                any(not torch.equal(value, a_adapter.state_dict()[key]) for key, value in immutable_a.items())):
            errors.append(f"{arm}:{arrival}:a_skill_mutation")
        state = {"A": {"left": a_adapter.left.detach().tolist(), "right": a_adapter.right.detach().tolist()},
                 "B": {"left": b_adapter.left.detach().tolist(), "right": b_adapter.right.detach().tolist()}}
        record = checkpoints[arrival] if arrival < len(checkpoints) else {}
        if (record.get("arrival") != arrival + 1 or record.get("skills") != state
                or record.get("skills_sha256") != sha(canonical(state))):
            errors.append(f"{arm}:{arrival}:skills")
        expected_optimizer = optimizer_json(optimizer, b_adapter)
        if record.get("optimizer") != expected_optimizer:
            errors.append(f"{arm}:{arrival}:optimizer")
        pred_a, pred_b = predictions(core, a_adapter, test_a), predictions(core, b_adapter, test_b)
        if record.get("pred_a") != pred_a or record.get("pred_b") != pred_b:
            errors.append(f"{arm}:{arrival}:predictions")
        curves["A"].append(sum(p == int(y) for p, y in zip(pred_a, a_labels(test_a).tolist())) / len(pred_a))
        curves["B"].append(sum(p == int(y) for p, y in zip(pred_b, b_labels(test_b).tolist())) / len(pred_b))
    durations = raw_arm.get("update_ns", [])
    if (raw_arm.get("optimizer_steps") != 128 or len(durations) != 128
            or any(not isinstance(v, int) or v <= 0 or v >= 60_000_000 for v in durations)):
        errors.append(f"{arm}:schedule_or_duration")
    if raw_arm.get("final_optimizer") != optimizer_json(optimizer, b_adapter):
        errors.append(f"{arm}:final_optimizer")
    expected_immutable = immutable_a is None or all(
            torch.equal(value, a_adapter.state_dict()[key]) for key, value in immutable_a.items())
    expected_identity = (not shared) if arm == "ROUTED_SEPARATE_SKILLS" else True
    if (raw_arm.get("a_adapter_immutable") is not expected_immutable
            or raw_arm.get("a_adapter_identity") is not expected_identity):
        errors.append(f"{arm}:adapter_identity")
    return errors, curves, max(durations) / 1_000_000 if durations else None


def run(formal_path, audit_path):
    root = Path(formal_path)
    raw_bytes = (root / "raw" / "formal_result.json").read_bytes()
    raw = json.loads(raw_bytes, object_pairs_hook=unique_pairs)
    freeze = load(Path(__file__).with_name("FREEZE.json"))
    errors, misses, results = [], [], []
    source = Path(__file__).resolve().parent
    for name, expected in freeze["source_sha256"].items():
        if sha((source / name).read_bytes()) != expected:
            errors.append("source_hash:" + name)
    freeze_bytes = (source / "FREEZE.json").read_bytes()
    if not valid_freeze_sidecar(Path(__file__).with_name("FREEZE.sha256").read_bytes(), freeze_bytes):
        errors.append("freeze_hash")
    if (freeze.get("allocation") != ALLOCATION or freeze.get("docker_image_id") != IMAGE
            or tuple(freeze.get("seeds", [])) != SEEDS):
        errors.append("freeze_identity")
    receipt = load(root / "FORMAL_INVOCATION.json")
    stdout, stderr = (root / "docker.stdout.bin").read_bytes(), (root / "docker.stderr.bin").read_bytes()
    if (receipt.get("allocation") != ALLOCATION or receipt.get("freeze_sha256") != sha(freeze_bytes)
            or receipt.get("image_id") != IMAGE or receipt.get("inspected_image") != IMAGE + " linux/amd64"
            or receipt.get("exit_code") != 0 or receipt.get("formal_orchestrations") != 1
            or receipt.get("retries") != 0 or receipt.get("raw_bytes") != len(raw_bytes)
            or receipt.get("raw_sha256") != sha(raw_bytes)
            or receipt.get("stdout_bytes") != len(stdout) or receipt.get("stdout_sha256") != sha(stdout)
            or receipt.get("stderr_bytes") != len(stderr) or receipt.get("stderr_sha256") != sha(stderr)):
        errors.append("formal_receipt_binding")
    argv = receipt.get("command_argv", [])
    required = ("--pull=never", "--network=none", "--read-only", "--cpus=1", "--memory=2g",
                "--pids-limit=64", IMAGE, "runner.py", "NEEDLE_SEEDS=9944211,9944311,9944411")
    if any(part not in argv for part in required) or not invocation_mounts_valid(argv):
        errors.append("formal_argv_or_mounts")
    if (raw.get("schema") != "needle-role-skill-joint-retention-raw-v2" or raw.get("allocation") != ALLOCATION
            or tuple(raw.get("seeds", [])) != SEEDS or tuple(raw.get("arms", [])) != ARMS):
        errors.append("raw_identity")
    env = raw.get("environment", {})
    if env.get("device") != "cpu" or env.get("threads") != 1 or env.get("interop_threads") != 1:
        errors.append("environment")
    if [item.get("seed") for item in raw.get("runs", [])] != list(SEEDS):
        errors.append("seed_denominator")
    for run_row in raw.get("runs", []):
        seed = run_row["seed"]
        core, train_x, train_y, schedule = make_base(seed)
        for parameter in core.parameters():
            parameter.requires_grad_(False)
        base = state_dict_json(core)
        if (run_row.get("base") != base or run_row.get("base_sha256") != sha(canonical(base))
                or run_row.get("base_after_sha256") != sha(canonical(base)) or run_row.get("base_immutable") is not True):
            errors.append(f"{seed}:base")
        memory, support = sample(16, seed, 202, 0), sample(16, seed, 303, 1)
        test_a, test_b = sample(256, seed, 404, 0), sample(256, seed, 505, 1)
        fields = (("base_train_x", train_x.tolist()), ("base_train_y", train_y.tolist()),
                  ("base_row_indices", schedule), ("memory_x", memory.tolist()),
                  ("memory_y", a_labels(memory).tolist()), ("support_x", support.tolist()),
                  ("support_y", b_labels(support).tolist()), ("test_a_x", test_a.tolist()),
                  ("test_a_y", a_labels(test_a).tolist()), ("test_b_x", test_b.tolist()),
                  ("test_b_y", b_labels(test_b).tolist()))
        expected_hash_keys = {key for key, _ in fields}
        if set(run_row.get("dataset_sha256", {})) != expected_hash_keys:
            errors.append(f"{seed}:dataset_hash_key_set")
        for key, value in fields:
            if run_row.get(key) != value:
                errors.append(f"{seed}:{key}")
            if run_row.get("dataset_sha256", {}).get(key) != sha(canonical(value)):
                errors.append(f"{seed}:{key}:digest")
        splits = [{tuple(row) for row in values.tolist()} for values in (train_x, memory, support, test_a, test_b)]
        if any(splits[i] & splits[j] for i in range(5) for j in range(i + 1, 5)):
            errors.append(f"{seed}:split_overlap")
        torch.manual_seed(seed + 500)
        init = {"left": (torch.randn(16, 2) * 0.1).tolist(), "right": torch.zeros(2, 4).tolist()}
        if run_row.get("init_adapter") != init:
            errors.append(f"{seed}:init")
        arms = {item.get("arm"): item for item in run_row.get("arms", [])}
        if set(arms) != set(ARMS):
            errors.append(f"{seed}:arms")
            continue
        final = {}
        for name in ARMS:
            arm_errors, curves, maximum = replay_arm(name, core, support, b_labels(support), memory,
                                                      a_labels(memory), test_a, test_b, init, arms[name])
            errors.extend(f"{seed}:{item}" for item in arm_errors)
            final[name] = {"A": curves["A"][-1], "B": curves["B"][-1], "max_update_ms": maximum}
        routed = final["ROUTED_SEPARATE_SKILLS"]
        if (routed["A"] < .90 or routed["B"] < .90
                or any(routed["A"] < final[name]["A"] + .10 for name in ARMS[:3])
                or routed["B"] < max(final[name]["B"] for name in ARMS[:3]) - .10):
            misses.append(f"{seed}:routed_A={routed['A']:.6f}:B={routed['B']:.6f}:comparators={final}")
        results.append({"seed": seed, "final": final})
    decision = ("HOLD_AUDIT_INTEGRITY" if errors else "FAIL_ROUTING_OR_RETENTION" if misses
                else "PASS_ROUTED_ONLINE_LORA_SKILLS_SCOPED")
    result = {"audit": "PASS_AUDIT" if not errors else "FAIL_AUDIT", "decision": decision,
              "errors": errors, "scientific_failures": misses, "n_seeds": len(results),
              "n_arm_arrival_rows": sum(len(a.get("arrivals", [])) for row in raw.get("runs", [])
                                        for a in row.get("arms", [])),
              "results": results,
              "thresholds": {"routed_A": .90, "routed_B": .90, "A_gain_each_shared": .10,
                             "routed_B_gap_to_best_shared": .10, "update_ms_strict": 60}}
    with Path(audit_path).open("xb") as output:
        output.write(canonical(result) + b"\n")
    print(json.dumps({"audit": result["audit"], "decision": decision,
                      "errors": len(errors), "scientific_failures": len(misses)}, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py FORMAL_DIR AUDIT_JSON")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    result = run(sys.argv[1], sys.argv[2])
    raise SystemExit(0 if result["audit"] == "PASS_AUDIT" else 2)

