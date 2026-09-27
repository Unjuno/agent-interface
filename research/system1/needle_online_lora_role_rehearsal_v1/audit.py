"""Independent raw-only replay; deliberately does not import runner.py."""
import hashlib
import json
import random
import statistics
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

SEEDS = (735211, 735311, 735411)
ARMS = ("B_ONLY", "B_DUPLICATE_CONTROL", "A_REHEARSAL")
ALLOCATION = "needle-online-lora-role-rehearsal-20260927-v1"
IMAGE = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(x):
    return hashlib.sha256(x).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)


def invocation_mounts_valid(argv):
    mounts = [argv[i + 1] for i, part in enumerate(argv[:-1]) if part == "--mount"]
    destinations = [mount.split(",dst=", 1)[1] if ",dst=" in mount else "" for mount in mounts]
    sources = [mount.split(",dst=", 1)[0].removeprefix("type=bind,source=")
               if mount.startswith("type=bind,source=") and ",dst=" in mount else ""
               for mount in mounts]
    return (len(mounts) == 2 and destinations == ["/src,readonly", "/out"]
            and bool(sources[0]) and bool(sources[1]) and sources[0] != sources[1]
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

    def forward(self, core, x):
        hidden = torch.tanh(core.enc(x))
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
        objective = F.cross_entropy(model(inputs[ix:ix + 1]), labels[ix:ix + 1])
        objective.backward()
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
    if arm == "B_ONLY":
        return bx.reshape(1, -1), by.reshape(1)
    if arm == "B_DUPLICATE_CONTROL":
        return bx.repeat(2, 1), by.repeat(2)
    if arm == "A_REHEARSAL":
        return torch.stack((bx, ax[mem_ix])), torch.stack((by, ay[mem_ix]))
    raise ValueError("unknown_arm")


def predictions(core, adapter, inputs):
    with torch.no_grad():
        return adapter(core, inputs).argmax(-1).tolist()


def replay_arm(seed, arm_name, core, support_x, support_y, memory_x, memory_y, test_a, test_b, init):
    adapter = AuditAdapter()
    with torch.no_grad():
        adapter.left.copy_(torch.tensor(init["left"], dtype=torch.float32))
        adapter.right.copy_(torch.tensor(init["right"], dtype=torch.float32))
    optimizer = torch.optim.AdamW(adapter.parameters(), lr=0.04, weight_decay=1e-4)
    errors, curves = [], {"A": [], "B": []}
    updates = []
    checkpoints = None
    raw_arm = None
    # Caller supplies checkpoints via a narrow attribute to keep this function's reconstruction-only API.
    checkpoints = CURRENT_ARM[arm_name].get("arrivals", [])
    for arrival in range(16):
        for step in range(8):
            index = arrival * 8 + step
            bx, by = support_x[arrival], support_y[arrival]
            inputs, labels = make_batch(arm_name, bx, by, memory_x, memory_y, index % 16)
            optimizer.zero_grad(set_to_none=True)
            F.cross_entropy(adapter(core, inputs), labels).backward()
            optimizer.step()
            updates.append(index)
        snapshot = {"left": adapter.left.detach().tolist(), "right": adapter.right.detach().tolist()}
        record = checkpoints[arrival]
        if record.get("arrival") != arrival + 1:
            errors.append(f"{seed}:{arm_name}:{arrival}:arrival")
        if record.get("adapter") != snapshot or record.get("adapter_sha256") != sha(canonical(snapshot)):
            errors.append(f"{seed}:{arm_name}:{arrival}:adapter")
        opt_state = optimizer_json(optimizer, adapter)
        if record.get("optimizer") != opt_state:
            errors.append(f"{seed}:{arm_name}:{arrival}:optimizer")
        pred_a, pred_b = predictions(core, adapter, test_a), predictions(core, adapter, test_b)
        if record.get("pred_a") != pred_a or record.get("pred_b") != pred_b:
            errors.append(f"{seed}:{arm_name}:{arrival}:prediction")
        curves["A"].append(sum(p == int(y) for p, y in zip(pred_a, a_labels(test_a).tolist())) / len(pred_a))
        curves["B"].append(sum(p == int(y) for p, y in zip(pred_b, b_labels(test_b).tolist())) / len(pred_b))
    duration = CURRENT_ARM[arm_name].get("update_ns", [])
    if (CURRENT_ARM[arm_name].get("optimizer_steps") != 128 or len(duration) != 128
            or any(not isinstance(value, int) or value <= 0 or value >= 60_000_000 for value in duration)):
        errors.append(f"{seed}:{arm_name}:update_schedule_or_duration")
    if CURRENT_ARM[arm_name].get("final_optimizer") != optimizer_json(optimizer, adapter):
        errors.append(f"{seed}:{arm_name}:final_optimizer")
    return errors, curves, max(duration) / 1_000_000


CURRENT_ARM = {}


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
    if sha(freeze_bytes) != (source / "FREEZE.sha256").read_text(encoding="ascii").strip():
        errors.append("freeze_hash")
    if freeze.get("allocation") != ALLOCATION or freeze.get("docker_image_id") != IMAGE:
        errors.append("freeze_identity")
    receipt = load(root / "FORMAL_INVOCATION.json")
    stdout = (root / "docker.stdout.bin").read_bytes()
    stderr = (root / "docker.stderr.bin").read_bytes()
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
                "--pids-limit=64", IMAGE, "runner.py", "NEEDLE_SEEDS=735211,735311,735411")
    if any(part not in argv for part in required):
        errors.append("formal_argv")
    if not invocation_mounts_valid(argv):
        errors.append("formal_mounts")
    if (raw.get("schema") != "needle-role-rehearsal-raw-v1" or raw.get("allocation") != ALLOCATION
            or tuple(raw.get("seeds", ())) != SEEDS or tuple(raw.get("arms", ())) != ARMS):
        errors.append("raw_identity")
    environment = raw.get("environment", {})
    if environment.get("device") != "cpu" or environment.get("threads") != 1 or environment.get("interop_threads") != 1:
        errors.append("environment")
    if [row.get("seed") for row in raw.get("runs", [])] != list(SEEDS):
        errors.append("seed_denominator")
    for run_row in raw.get("runs", []):
        seed = run_row["seed"]
        core, train_x, train_y, schedule = make_base(seed)
        for parameter in core.parameters():
            parameter.requires_grad_(False)
        base = state_dict_json(core)
        if (run_row.get("base") != base or run_row.get("base_sha256") != sha(canonical(base))
                or run_row.get("base_after_sha256") != sha(canonical(base)) or run_row.get("base_immutable") is not True):
            errors.append(f"{seed}:base_replay_or_immutability")
        memory = sample(16, seed, 202, 0)
        support = sample(16, seed, 303, 1)
        test_a, test_b = sample(256, seed, 404, 0), sample(256, seed, 505, 1)
        memory_y, support_y = a_labels(memory), b_labels(support)
        splits = [{tuple(row) for row in data.tolist()} for data in (train_x, memory, support, test_a, test_b)]
        if any(splits[i] & splits[j] for i in range(len(splits)) for j in range(i + 1, len(splits))):
            errors.append(f"{seed}:split_overlap")
        expected_fields = (("base_train_x", train_x.tolist()), ("base_train_y", train_y.tolist()),
                           ("base_row_indices", schedule), ("memory_x", memory.tolist()),
                           ("memory_y", memory_y.tolist()), ("support_x", support.tolist()),
                           ("support_y", support_y.tolist()), ("test_a_x", test_a.tolist()),
                           ("test_a_y", a_labels(test_a).tolist()), ("test_b_x", test_b.tolist()),
                           ("test_b_y", b_labels(test_b).tolist()))
        for key, value in expected_fields:
            if run_row.get(key) != value:
                errors.append(f"{seed}:{key}")
        torch.manual_seed(seed + 500)
        expected_init = {"left": (torch.randn(16, 2) * 0.1).tolist(), "right": torch.zeros(2, 4).tolist()}
        # Init regeneration above deliberately uses a local RNG reset, not producer state.
        if run_row.get("init_adapter") != expected_init:
            errors.append(f"{seed}:initial_adapter")
        if run_row.get("invalid_controls") != [
            {"status": "YIELD", "selected_role": None, "proposal": None},
            {"status": "YIELD", "selected_role": None, "proposal": None}]:
            errors.append(f"{seed}:invalid_controls")
        arms = {arm.get("arm"): arm for arm in run_row.get("arms", [])}
        if set(arms) != set(ARMS):
            errors.append(f"{seed}:arm_set")
            continue
        accuracy = {}
        for arm_name in ARMS:
            CURRENT_ARM[arm_name] = arms[arm_name]
            arm_errors, curves, max_ms = replay_arm(seed, arm_name, core, support, support_y,
                                                    memory, memory_y, test_a, test_b,
                                                    run_row["init_adapter"])
            errors.extend(arm_errors)
            accuracy[arm_name] = curves
            accuracy[arm_name]["max_update_ms"] = max_ms
        if arms["B_DUPLICATE_CONTROL"].get("arrivals") != arms["B_ONLY"].get("arrivals"):
            errors.append(f"{seed}:duplicate_control_not_equivalent")
        final = {arm: {"A": curves["A"][-1], "B": curves["B"][-1],
                       "max_update_ms": curves["max_update_ms"]} for arm, curves in accuracy.items()}
        if final["B_ONLY"]["B"] < 0.85:
            misses.append(f"{seed}:B_ONLY_B={final['B_ONLY']['B']:.6f}")
        if final["B_DUPLICATE_CONTROL"]["B"] < 0.85:
            misses.append(f"{seed}:DUP_B={final['B_DUPLICATE_CONTROL']['B']:.6f}")
        if (final["A_REHEARSAL"]["A"] < 0.90 or final["A_REHEARSAL"]["B"] < 0.90
                or final["A_REHEARSAL"]["B"] < final["B_DUPLICATE_CONTROL"]["B"] - 0.10):
            misses.append(f"{seed}:REHEARSAL_A={final['A_REHEARSAL']['A']:.6f}:B={final['A_REHEARSAL']['B']:.6f}")
        results.append({"seed": seed, "final": final, "curves": accuracy})
    mean_gain = None
    if not errors and len(results) == len(SEEDS):
        mean_gain = statistics.mean(r["final"]["A_REHEARSAL"]["A"] - r["final"]["B_DUPLICATE_CONTROL"]["A"] for r in results)
        if mean_gain < 0.10:
            misses.append(f"mean_A_rehearsal_gain={mean_gain:.6f}")
    decision = "HOLD_AUDIT_INTEGRITY" if errors else "FAIL_REHEARSAL_QUALITY" if misses else "PASS_ROLE_CONDITIONED_REHEARSAL_SCOPED"
    result = {"audit": "PASS_AUDIT" if not errors else "FAIL_AUDIT", "decision": decision,
              "errors": errors, "scientific_failures": misses, "n_seeds": len(results),
              "n_arm_arrival_rows": sum(len(arm.get("arrivals", [])) for row in raw.get("runs", []) for arm in row.get("arms", [])),
              "observed_mean_A_gain": mean_gain, "results": results,
              "thresholds": {"rehearsal_A": 0.90, "rehearsal_B": 0.90, "duplicate_B_floor": 0.85,
                             "B_gap": 0.10, "mean_A_gain": 0.10, "max_update_ms_strict": 60}}
    output = Path(audit_path)
    with output.open("xb") as stream:
        stream.write(canonical(result) + b"\n")
    print(json.dumps({"audit": result["audit"], "decision": decision,
                      "errors": len(errors), "scientific_failures": len(misses)}, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py FORMAL_DIR AUDIT_JSON")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    result = run(sys.argv[1], sys.argv[2])
    raise SystemExit(0 if result["audit"] == "PASS_AUDIT" else 2)
