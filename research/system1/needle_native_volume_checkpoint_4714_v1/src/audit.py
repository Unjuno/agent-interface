#!/usr/bin/env python3
"""Independent exact-resume auditor; intentionally does not import study.py."""
import argparse
import hashlib
import json
from pathlib import Path

import torch
from torch import nn
import torch.nn.functional as F

SEEDS = (6842731, 6842733, 6842737)
CONSTRUCTION_SEED = 6842703
D, H, C = 8, 16, 4
UPDATES, ARRIVALS, N_SUPPORT = 8, 12, 16
LR = 0.04
SCHEMA = "needle-resident-snapshot-v1"


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(x):
    return hashlib.sha256(canonical(x)).hexdigest()


def labels(x):
    return (1 - (x[:, 0] > 0).long()) * 2 + (x[:, 1] > 0).long()


class Core(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(D, H), nn.Tanh())
        self.head = nn.Linear(H, C)

    def forward(self, x):
        return self.head(self.enc(x))


class Adapted(nn.Module):
    def __init__(self, core):
        super().__init__()
        self.core = core
        for p in core.parameters():
            p.requires_grad_(False)
        self.a = nn.Parameter(torch.zeros(H, 2))
        self.b = nn.Parameter(torch.zeros(2, C))

    def forward(self, x):
        z = self.core.enc(x)
        return self.core.head(z) + (z @ self.a @ self.b) / 2


def opt_record(m, opt):
    out = {"step": 0}
    for name, p in (("a", m.a), ("b", m.b)):
        s = opt.state.get(p)
        out[f"avg_{name}"] = s["exp_avg"].tolist() if s else torch.zeros_like(p).tolist()
        out[f"sq_{name}"] = s["exp_avg_sq"].tolist() if s else torch.zeros_like(p).tolist()
        if s:
            out["step"] = int(s["step"].item())
    return out


def initial(raw):
    core = Core()
    core.load_state_dict({k: torch.tensor(v) for k, v in raw["base_state"].items()})
    m = Adapted(core)
    with torch.no_grad():
        m.a.copy_(torch.tensor(raw["initial_adapter"]["a"]))
        m.b.copy_(torch.tensor(raw["initial_adapter"]["b"]))
    return m, torch.optim.AdamW([m.a, m.b], lr=LR)


def snapshot(seed, base_sha, cursor, m, opt):
    x = {"schema": SCHEMA, "allocation": "needle-native-volume-checkpoint-6842731-6842733-6842737-v1",
         "seed": seed, "role": "B", "base_sha256": base_sha, "cursor": cursor,
         "adapter": {"a": m.a.detach().cpu().tolist(), "b": m.b.detach().cpu().tolist()}, "optimizer": opt_record(m, opt)}
    x["snapshot_sha256"] = digest(x)
    return x


def validate_snapshot(s, seed, base_sha, cursor):
    body = dict(s)
    claimed = body.pop("snapshot_sha256", None)
    if claimed != digest(body):
        raise ValueError("snapshot_digest")
    if s.get("schema") != SCHEMA or s.get("role") != "B":
        raise ValueError("snapshot_schema_or_role")
    if s.get("seed") != seed or s.get("base_sha256") != base_sha or s.get("cursor") != cursor:
        raise ValueError("snapshot_binding")
    if s.get("optimizer", {}).get("step") != cursor * UPDATES:
        raise ValueError("snapshot_step")


def p95(values):
    return sorted(values)[max(0, __import__("math").ceil(0.95 * len(values)) - 1)]


def p50(values):
    return sorted(values)[max(0, __import__("math").ceil(0.5 * len(values)) - 1)]


def calc(raw):
    m, opt = initial(raw)
    xs = torch.tensor(raw["x_support"], dtype=torch.float32)
    xe = torch.tensor(raw["x_eval"], dtype=torch.float32)
    records = []
    for cur, entry in enumerate(raw["schedule"]):
        rows = [entry["row"]]
        local_x = xs[rows]
        local_y = torch.tensor([labels(local_x[j:j + 1])[0].item()
                                for j in range(len(rows))], dtype=torch.long)
        for _ in range(UPDATES):
            loss = F.cross_entropy(m(local_x), local_y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
        with torch.no_grad():
            pred = m(xe).argmax(-1).tolist()
        records.append({"snapshot": snapshot(raw["seed"], raw["base_sha256"], cur + 1, m, opt),
                        "prediction": pred})
    return records


def audit(root, output, volume_root, smoke_one=False, construction_full=False):
    errors, checked, reports = [], 0, []
    seeds = (CONSTRUCTION_SEED,) if (smoke_one or construction_full) else SEEDS
    arrivals = 1 if smoke_one else ARRIVALS
    for seed in seeds:
        result = json.loads((Path(root) / f"seed_{seed}.json").read_text(encoding="utf-8"))
        raw = result["input"]
        if raw["seed"] != seed or raw["allocation"] != "needle-native-volume-checkpoint-6842731-6842733-6842737-v1":
            errors.append(f"{seed}:input_identity")
        if "y_support" in raw or "y_eval" in raw:
            errors.append(f"{seed}:future_label_leak")
        order = [entry["row"] for entry in raw["schedule"]]
        if len(raw["schedule"]) != N_SUPPORT:
            errors.append(f"{seed}:support_schedule_count")
        if result.get("arrival_count") != arrivals:
            errors.append(f"{seed}:run_arrival_count")
        for cur, entry in enumerate(raw["schedule"][:arrivals]):
            if (entry["seen"] != order[:cur + 1] or entry["row"] != order[cur] or
                    entry["batches"] != [[entry["row"]] for _ in range(UPDATES)]):
                errors.append(f"{seed}:revealed_support_schedule:{cur}")
        for arm in ("bind", "volume"):
            if len(result["arms"][arm]) != arrivals:
                errors.append(f"{seed}:{arm}:arrival_count")
        worker_input = json.loads((Path(root) / str(seed) / "input.json").read_text(encoding="utf-8"))
        if any(k in worker_input for k in ("x_support", "schedule", "y_support", "y_eval")):
            errors.append(f"{seed}:worker_future_information")
        expected = calc(raw)[:arrivals]
        raw_hash_body = dict(raw)
        raw_claim = raw_hash_body.pop("input_sha256", None)
        if raw_claim != digest(raw_hash_body) or digest(raw["base_state"]) != raw["base_sha256"]:
            errors.append(f"{seed}:input_or_base_digest")
        for cursor, ref in enumerate(expected):
            for arm in ("bind", "volume"):
                if cursor >= len(result["arms"][arm]):
                    errors.append(f"{seed}:{arm}:{cursor}:missing_arrival")
                    continue
                got = result["arms"][arm][cursor]
                checked += 1
                expected_row = raw["schedule"][cursor]["row"]
                expected_x = raw["x_support"][expected_row]
                expected_y = labels(torch.tensor([expected_x], dtype=torch.float32))[0].item()
                request = got.get("request", {})
                if (request.get("cursor") != cursor or request.get("row") != expected_row or
                        request.get("x") != expected_x or request.get("y") != expected_y):
                    errors.append(f"{seed}:{arm}:{cursor}:request_binding")
                if got["cursor"] != cursor + 1 or got["snapshot"] != ref["snapshot"]:
                    errors.append(f"{seed}:{arm}:{cursor}:snapshot")
                if got["prediction"] != ref["prediction"]:
                    errors.append(f"{seed}:{arm}:{cursor}:prediction")
                s = got["snapshot"]
                try:
                    validate_snapshot(s, seed, raw["base_sha256"], cursor + 1)
                except ValueError as e:
                    errors.append(f"{seed}:{arm}:{cursor}:{e}")
                durable_bytes = canonical(s) + b"\n"
                if got["disk_sha256"] != hashlib.sha256(durable_bytes).hexdigest():
                    errors.append(f"{seed}:{arm}:{cursor}:durable_bytes_digest")
        if any(not c["bind_snapshot_match"] or not c["volume_snapshot_match"] or
               not c["bind_prediction_match"] or not c["volume_prediction_match"]
               for c in result["comparisons"]):
            errors.append(f"{seed}:runner_comparison")
        bs = [x["response_ns"] for x in result["arms"]["bind"]]
        vs = [x["response_ns"] for x in result["arms"]["volume"]]
        bind_commit = [x["commit_ns"] for x in result["arms"]["bind"]]
        volume_commit = [x["commit_ns"] for x in result["arms"]["volume"]]
        bind_update = [x["update_ns"] for x in result["arms"]["bind"]]
        volume_update = [x["update_ns"] for x in result["arms"]["volume"]]
        bind_prediction = [x["prediction_ns"] for x in result["arms"]["bind"]]
        volume_prediction = [x["prediction_ns"] for x in result["arms"]["volume"]]
        bind_disk = Path(root) / "checkpoints" / str(seed) / "bind" / "snapshot.json"
        volume_disk = Path(volume_root) / str(seed) / "volume" / "snapshot.json"
        volume_bytes = None
        for arm, path in (("bind", bind_disk), ("volume", volume_disk)):
            try:
                disk_raw = path.read_bytes()
                if arm == "volume":
                    volume_bytes = disk_raw
                if not result["arms"][arm]:
                    errors.append(f"{seed}:{arm}:empty_arm")
                    continue
                final_snapshot = result["arms"][arm][-1]["snapshot"]
                if disk_raw != canonical(final_snapshot) + b"\n":
                    errors.append(f"{seed}:{arm}:final_checkpoint_bytes")
            except OSError:
                errors.append(f"{seed}:{arm}:final_checkpoint_missing")
        volume_final_sha = None
        if volume_bytes is not None:
            retained = Path(output) / "volume-final" / str(seed) / "snapshot.json"
            retained.parent.mkdir(parents=True, exist_ok=True)
            with retained.open("xb") as f:
                f.write(volume_bytes)
                f.flush()
            volume_final_sha = hashlib.sha256(volume_bytes).hexdigest()
            if hashlib.sha256(retained.read_bytes()).hexdigest() != volume_final_sha:
                errors.append(f"{seed}:retained_volume_copy_hash")
        reports.append({"seed": seed, "arrivals": len(result["comparisons"]),
                        "bind_p95_ms": p95(bs) / 1e6,
                        "volume_p95_ms": p95(vs) / 1e6,
                        "p95_ratio": p95(vs) / max(1, p95(bs)),
                        "bind_commit_p50_ms": p50(bind_commit) / 1e6,
                        "bind_commit_p95_ms": p95(bind_commit) / 1e6,
                        "volume_commit_p50_ms": p50(volume_commit) / 1e6,
                        "volume_commit_p95_ms": p95(volume_commit) / 1e6,
                        "bind_update_p50_ms": p50(bind_update) / 1e6,
                        "volume_update_p50_ms": p50(volume_update) / 1e6,
                        "bind_prediction_p50_ms": p50(bind_prediction) / 1e6,
                        "bind_prediction_p95_ms": p95(bind_prediction) / 1e6,
                        "volume_prediction_p50_ms": p50(volume_prediction) / 1e6,
                        "volume_prediction_p95_ms": p95(volume_prediction) / 1e6,
                        "volume_final_sha256": volume_final_sha,
                        "startup_ms": {k: v / 1e6 for k, v in result["startup_ns"].items()},
                        "bind_ms": [x / 1e6 for x in bs],
                        "volume_ms": [x / 1e6 for x in vs]})
    # Mutate copies and require the independent binding validator to reject each one.
    sample_result = json.loads((Path(root) / f"seed_{seeds[0]}.json").read_text(encoding="utf-8"))
    sample = sample_result["arms"]["volume"][0]["snapshot"]
    controls = {}
    for name, change in (
        ("digest", lambda x: x.update(snapshot_sha256="0" * 64)),
        ("seed", lambda x: x.update(seed=x["seed"] + 1)),
        ("role", lambda x: x.update(role="A")),
        ("base", lambda x: x.update(base_sha256="f" * 64)),
        ("cursor", lambda x: x.update(cursor=x["cursor"] + 1)),
    ):
        corrupted = json.loads(json.dumps(sample))
        change(corrupted)
        if name != "digest":
            body = dict(corrupted)
            body.pop("snapshot_sha256", None)
            corrupted["snapshot_sha256"] = digest(body)
        try:
            validate_snapshot(corrupted, seeds[0], sample["base_sha256"], 1)
            controls[name] = False
        except ValueError:
            controls[name] = True
    integrity_ok = not errors and checked == len(seeds) * arrivals * 2 and all(controls.values())
    gates = not smoke_one and not construction_full and integrity_ok and all(r["volume_p95_ms"] <= 60 and r["p95_ratio"] <= 0.5
                                 for r in reports)
    decision = ("PASS_NATIVE_VOLUME_LATENCY_SCOPED" if gates else
                "CONSTRUCTION_ONLY_AUDIT_PASS" if construction_full and integrity_ok else
                "HOLD_LATENCY_BUDGET" if integrity_ok else "STOP_AUDIT_OR_INTEGRITY")
    report = {"schema": "needle-native-volume-audit-v1", "checked_snapshots": checked,
              "corruption_controls_rejected": sum(controls.values()), "controls": controls,
              "errors": errors, "seeds": reports,
              "integrity_pass": integrity_ok, "decision": decision}
    out = Path(output) / "AUDIT.json"
    with out.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--volume-root", required=True)
    ap.add_argument("--smoke-one", action="store_true")
    ap.add_argument("--construction-full", action="store_true")
    a = ap.parse_args()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    report = audit(a.raw, a.out, a.volume_root, a.smoke_one, a.construction_full)
    print(json.dumps({"decision": report["decision"], "errors": len(report["errors"]),
                      "checked_snapshots": report["checked_snapshots"]}, sort_keys=True), flush=True)
    if report["decision"] in ("STOP_AUDIT_OR_INTEGRITY",):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
