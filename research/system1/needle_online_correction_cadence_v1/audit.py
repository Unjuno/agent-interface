"""Independent raw replay; imports neither runner.py nor its model classes."""
import hashlib
import json
import random
import statistics
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

SEEDS = (734211, 734311, 734411)
ARMS = ("SINGLE", "MICROBATCH2")
ROLES = ("A", "B")
ALLOCATION = "needle-online-correction-cadence-20260927-v1"
EXPECTED_IMAGE = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pairs_no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate_json_key")
        out[key] = value
    return out


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs_no_duplicates)


def tensor_json(module):
    return {k: v.detach().cpu().tolist() for k, v in module.state_dict().items()}


def sample(rows, seed, salt):
    rng = random.Random(seed * 1009 + salt)
    factors = [0, 1] * (rows // 2)
    rng.shuffle(factors)
    return torch.tensor([[float(bit), *[rng.random() for _ in range(7)]] for bit in factors],
                        dtype=torch.float32)


def b_labels(x):
    return 1 - x[:, 0].long()


def a_labels(x):
    return x[:, 0].long()


class AuditCore(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = torch.nn.Linear(8, 16)
        self.head = torch.nn.Linear(16, 4)

    def forward(self, x):
        hidden = torch.tanh(self.enc(x))
        return self.head(hidden)


class AuditAdapter(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.left = torch.nn.Parameter(torch.empty(16, 2))
        self.right = torch.nn.Parameter(torch.empty(2, 4))

    def forward(self, core, x):
        h = torch.tanh(core.enc(x))
        return core.head(h) + h @ self.left @ self.right / 2


def regenerate_base(seed):
    torch.manual_seed(seed)
    core = AuditCore()
    x = sample(256, seed, 101)
    y = a_labels(x)
    indices = torch.randint(len(x), (400,), generator=torch.Generator().manual_seed(seed + 102)).tolist()
    opt = torch.optim.AdamW(core.parameters(), lr=0.03, weight_decay=1e-4)
    for index in indices:
        opt.zero_grad(set_to_none=True)
        loss = F.cross_entropy(core(x[index:index + 1]), y[index:index + 1])
        loss.backward()
        opt.step()
    return core, x, y, indices


def regenerate_support(seed):
    x = sample(16, seed, 202)
    return x, b_labels(x)


def regenerated_init(seed):
    torch.manual_seed(seed + 500)
    return {"left": (torch.randn(16, 2) * 0.1).tolist(),
            "right": torch.zeros(2, 4).tolist()}


def actual_optimizer_state(opt, adapter):
    result = {}
    for name, parameter in (("left", adapter.left), ("right", adapter.right)):
        state = opt.state.get(parameter, {})
        result[name] = {
            "step": float(state["step"].item()) if "step" in state else 0.0,
            "exp_avg": state["exp_avg"].tolist() if "exp_avg" in state else None,
            "exp_avg_sq": state["exp_avg_sq"].tolist() if "exp_avg_sq" in state else None,
        }
    return result


def predict(core, adapter, x):
    with torch.no_grad():
        return adapter(core, x).argmax(-1).tolist()


def audit_arm(core, seed, arm_name, arm_raw, initial, support, support_y, test_a, test_b):
    adapter = AuditAdapter()
    with torch.no_grad():
        adapter.left.copy_(torch.tensor(initial["left"], dtype=torch.float32))
        adapter.right.copy_(torch.tensor(initial["right"], dtype=torch.float32))
    opt = torch.optim.AdamW(adapter.parameters(), lr=0.04, weight_decay=1e-4)
    errors, accuracies, expected_ns = [], {"A": [], "B": []}, 0
    expected_bursts = []
    checkpoints = arm_raw.get("arrivals", [])
    if len(checkpoints) != 16:
        return [f"{seed}:{arm_name}:arrival_count"], accuracies
    for ix in range(16):
        rows = [ix] if arm_name == "SINGLE" else ([ix - 1, ix] if ix % 2 == 1 else [])
        steps = 8 if arm_name == "SINGLE" else (16 if ix % 2 == 1 else 0)
        if rows:
            idx = torch.tensor(rows, dtype=torch.long)
            for _ in range(steps):
                expected_ns += 1
                opt.zero_grad(set_to_none=True)
                loss = F.cross_entropy(adapter(core, support[idx]), support_y[idx])
                loss.backward()
                opt.step()
        expected_bursts.append(steps)
        row = checkpoints[ix]
        current = {"left": adapter.left.detach().tolist(), "right": adapter.right.detach().tolist()}
        if row.get("arrival") != ix + 1 or row.get("updated") is not bool(rows):
            errors.append(f"{seed}:{arm_name}:{ix}:arrival_or_update_flag")
        if row.get("adapter") != current or row.get("adapter_sha256") != sha(canonical(current)):
            errors.append(f"{seed}:{arm_name}:{ix}:adapter_state")
        state = actual_optimizer_state(opt, adapter)
        if row.get("optimizer") != state:
            errors.append(f"{seed}:{arm_name}:{ix}:optimizer_state")
        pred_a = predict(core, adapter, test_a)
        pred_b = predict(core, adapter, test_b)
        if row.get("pred_a") != pred_a or row.get("pred_b") != pred_b:
            errors.append(f"{seed}:{arm_name}:{ix}:prediction")
        gold_a, gold_b = a_labels(test_a).tolist(), b_labels(test_b).tolist()
        acc_a = sum(a == b for a, b in zip(pred_a, gold_a)) / len(gold_a)
        acc_b = sum(a == b for a, b in zip(pred_b, gold_b)) / len(gold_b)
        accuracies["A"].append(acc_a)
        accuracies["B"].append(acc_b)
    ns = arm_raw.get("update_ns", [])
    if len(ns) != expected_ns or arm_raw.get("optimizer_steps") != expected_ns:
        errors.append(f"{seed}:{arm_name}:optimizer_step_count")
    burst_ns = arm_raw.get("burst_ns", [])
    if len(burst_ns) != 16 or any((steps == 0 and duration != 0) or (steps > 0 and duration <= 0)
                                  for steps, duration in zip(expected_bursts, burst_ns)):
        errors.append(f"{seed}:{arm_name}:burst_duration_receipt")
    if any(not isinstance(x, int) or x <= 0 or x >= 60_000_000 for x in ns):
        errors.append(f"{seed}:{arm_name}:update_duration_gate")
    if arm_raw.get("final_optimizer") != actual_optimizer_state(opt, adapter):
        errors.append(f"{seed}:{arm_name}:final_optimizer")
    return errors, accuracies


def audit(formal_root, audit_path):
    formal_root = Path(formal_root)
    raw_path = formal_root / "raw" / "formal_result.json"
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes, object_pairs_hook=pairs_no_duplicates)
    source = Path(__file__).resolve().parent
    freeze = load(source / "FREEZE.json")
    errors, rows, failures = [], [], []
    for filename, expected in freeze["source_sha256"].items():
        if sha((source / filename).read_bytes()) != expected:
            errors.append("source_hash:" + filename)
    if sha((source / "FREEZE.json").read_bytes()) != (source / "FREEZE.sha256").read_text(encoding="ascii").strip():
        errors.append("freeze_hash")
    if freeze.get("allocation") != ALLOCATION or freeze.get("docker_image_id") != EXPECTED_IMAGE:
        errors.append("freeze_identity")
    receipt = load(formal_root / "FORMAL_INVOCATION.json")
    if (receipt.get("allocation") != ALLOCATION or receipt.get("image_id") != EXPECTED_IMAGE
            or receipt.get("freeze_sha256") != sha((source / "FREEZE.json").read_bytes())
            or receipt.get("inspected_image") != EXPECTED_IMAGE + " linux/amd64"
            or receipt.get("exit_code") != 0 or receipt.get("formal_orchestrations") != 1
            or receipt.get("retries") != 0):
        errors.append("invocation_contract")
    stdout = (formal_root / "docker.stdout.bin").read_bytes()
    stderr = (formal_root / "docker.stderr.bin").read_bytes()
    if (receipt.get("raw_bytes") != len(raw_bytes) or receipt.get("raw_sha256") != sha(raw_bytes)
            or receipt.get("stdout_bytes") != len(stdout) or receipt.get("stdout_sha256") != sha(stdout)
            or receipt.get("stderr_bytes") != len(stderr) or receipt.get("stderr_sha256") != sha(stderr)):
        errors.append("invocation_retained_byte_hashes")
    argv = receipt.get("command_argv", [])
    required_argv = ("--pull=never", "--network=none", "--read-only", "--cpus=1", "--memory=2g",
                     "--pids-limit=64", "--security-opt=no-new-privileges", "NEEDLE_OUTPUT=/out",
                     "NEEDLE_SEEDS=734211,734311,734411", EXPECTED_IMAGE, "runner.py")
    if any(part not in argv for part in required_argv):
        errors.append("invocation_command")
    mounts = [argv[ix + 1] for ix, part in enumerate(argv[:-1]) if part == "--mount"]
    if (len(mounts) != 2 or 
            not mounts[0].endswith("needle_online_correction_cadence_v1,dst=/src,readonly") or
            not mounts[1].endswith("needle_online_correction_cadence_v1/formal/raw,dst=/out")):
        errors.append("invocation_mounts")
    if raw.get("schema") != "needle-online-cadence-raw-v1" or raw.get("allocation") != ALLOCATION:
        errors.append("raw_identity")
    if tuple(raw.get("seeds", [])) != SEEDS:
        errors.append("raw_seed_block")
    env = raw.get("environment", {})
    if env.get("device") != "cpu" or env.get("threads") != 1 or env.get("interop_threads") != 1:
        errors.append("environment")
    runs = raw.get("runs", [])
    if [r.get("seed") for r in runs] != list(SEEDS):
        errors.append("run_denominator")
    for run in runs:
        seed = run["seed"]
        core, base_train_x, base_train_y, base_indices = regenerate_base(seed)
        for parameter in core.parameters():
            parameter.requires_grad_(False)
        base = tensor_json(core)
        if run.get("base") != base or run.get("base_sha256") != sha(canonical(base)):
            errors.append(f"{seed}:base_replay")
        if run.get("base_immutable") is not True or run.get("base_after_sha256") != sha(canonical(base)):
            errors.append(f"{seed}:base_mutation")
        support, support_y = regenerate_support(seed)
        test_a, test_b = sample(256, seed, 303), sample(256, seed, 404)
        split_rows = [{tuple(row) for row in values.tolist()}
                      for values in (base_train_x, support, test_a, test_b)]
        if any(split_rows[i] & split_rows[j] for i in range(4) for j in range(i + 1, 4)):
            errors.append(f"{seed}:cross_split_row_overlap")
        if (run.get("base_train_x") != base_train_x.tolist()
                or run.get("base_train_y") != base_train_y.tolist()
                or run.get("base_row_indices") != base_indices):
            errors.append(f"{seed}:base_training_data_or_schedule")
        if run.get("support_x") != support.tolist() or run.get("support_y") != support_y.tolist():
            errors.append(f"{seed}:support_replay")
        if run.get("test_a_x") != test_a.tolist() or run.get("test_b_x") != test_b.tolist():
            errors.append(f"{seed}:test_inputs")
        if run.get("test_a_y") != a_labels(test_a).tolist() or run.get("test_b_y") != b_labels(test_b).tolist():
            errors.append(f"{seed}:heldout_labels")
        expected_init = regenerated_init(seed)
        if run.get("init_adapter") != expected_init:
            errors.append(f"{seed}:init_adapter")
        expected_controls = [
            {"status": "YIELD", "selected_role": None, "proposal": None},
            {"status": "YIELD", "selected_role": None, "proposal": None},
        ]
        if run.get("invalid_controls") != expected_controls:
            errors.append(f"{seed}:invalid_scope_controls")
        arm_map = {a.get("arm"): a for a in run.get("arms", [])}
        if set(arm_map) != set(ARMS):
            errors.append(f"{seed}:arm_set")
            continue
        seed_acc = {}
        for arm in ARMS:
            arm_errors, acc = audit_arm(core, seed, arm, arm_map[arm], expected_init,
                                        support, support_y, test_a, test_b)
            errors.extend(arm_errors)
            seed_acc[arm] = acc
            final_a, final_b = acc["A"][-1], acc["B"][-1]
            if arm == "MICROBATCH2" and (final_a < 0.90 or final_b < 0.90):
                failures.append(f"{seed}:{arm}:final_A={final_a:.6f}:final_B={final_b:.6f}")
            if arm == "SINGLE" and final_b < 0.85:
                failures.append(f"{seed}:SINGLE:final_B={final_b:.6f}")
        if seed_acc.get("MICROBATCH2", {}).get("B") and seed_acc.get("SINGLE", {}).get("B"):
            gap = seed_acc["SINGLE"]["B"][-1] - seed_acc["MICROBATCH2"]["B"][-1]
            if gap > 0.10:
                failures.append(f"{seed}:MICROBATCH2_B_gap={gap:.6f}")
        rows.append({"seed": seed, "arms": {arm: {
            "updates": arm_map[arm]["optimizer_steps"],
            "final_A_accuracy": seed_acc.get(arm, {}).get("A", [None])[-1],
            "final_B_accuracy": seed_acc.get(arm, {}).get("B", [None])[-1],
            "A_curve": seed_acc.get(arm, {}).get("A", []),
            "B_curve": seed_acc.get(arm, {}).get("B", []),
            "max_update_ms": max(arm_map[arm].get("update_ns", [0])) / 1_000_000,
            "max_burst_ms": max(arm_map[arm].get("burst_ns", [0])) / 1_000_000,
        } for arm in ARMS}})
    by_arm_a = {arm: [row["arms"][arm]["final_A_accuracy"] for row in rows] for arm in ARMS}
    mean_gain = None
    if not errors and len(rows) == len(SEEDS):
        mean_gain = statistics.mean(by_arm_a["MICROBATCH2"]) - statistics.mean(by_arm_a["SINGLE"])
        if mean_gain < 0.05:
            failures.append(f"microbatch2_mean_A_retention_gain={mean_gain:.6f}")
    decision = ("HOLD_AUDIT_INTEGRITY" if errors else
                "FAIL_SCHEDULE_QUALITY_OR_RETENTION" if failures else
                "PASS_ONLINE_MICROBATCH_TRADEOFF_SCOPED")
    result = {"audit": "PASS_AUDIT" if not errors else "FAIL_AUDIT", "decision": decision,
              "errors": errors, "scientific_failures": failures, "n_seeds": len(runs),
              "n_arm_arrival_rows": sum(len(a.get("arrivals", [])) for r in runs for a in r.get("arms", [])),
              "results": rows, "thresholds": {"single_final_B": 0.85, "microbatch2_final_A": 0.90,
                                                "microbatch2_final_B": 0.90, "microbatch2_B_gap": 0.10,
                                                "microbatch2_mean_A_gain": 0.05,
                                                "observed_mean_A_gain": mean_gain,
                                                "update_ms_strict_max": 60}}
    out = Path(audit_path)
    with out.open("xb") as f:
        f.write(canonical(result) + b"\n")
    print(json.dumps({"audit": result["audit"], "decision": decision,
                      "errors": len(errors), "scientific_failures": len(failures)}, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py FORMAL_ROOT AUDIT_JSON")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    result = audit(sys.argv[1], sys.argv[2])
    raise SystemExit(0 if result["audit"] == "PASS_AUDIT" else 2)
