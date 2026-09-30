#!/usr/bin/env python3
"""Independent audit for Issue #4732; does not import runner.py."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

import torch
import torch.nn.functional as F

sys.path.insert(0, "/baseline")
import study as source  # frozen data/model architecture only

ALLOCATION = "needle-single-query-ack-6842791-6842793-6842797-v1"
CONSTRUCTION_SEED = 6842783
FORMAL_SEEDS = (6842791, 6842793, 6842797)
MODES = ("INLINE_512", "ONLINE_QUERY_ONLY")


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(x):
    return hashlib.sha256(canon(x)).hexdigest()


def state_dict(model):
    return {k: v.detach().cpu().tolist() for k, v in model.state_dict().items()}


def optimizer_state(model, opt):
    result = {"step": 0}
    for name, param in (("a", model.a), ("b", model.b)):
        slot = opt.state.get(param)
        if slot is None:
            result[f"avg_{name}"] = torch.zeros_like(param).tolist()
            result[f"sq_{name}"] = torch.zeros_like(param).tolist()
        else:
            result["step"] = int(slot["step"].item())
            result[f"avg_{name}"] = slot["exp_avg"].detach().cpu().tolist()
            result[f"sq_{name}"] = slot["exp_avg_sq"].detach().cpu().tolist()
    return result


def expected_snapshot(seed, base_sha, cursor, model, opt):
    s = {"schema": source.SCHEMA, "allocation": source.ALLOCATION, "seed": seed,
         "role": "B", "base_sha256": base_sha, "cursor": cursor,
         "adapter": {"a": model.a.detach().cpu().tolist(),
                     "b": model.b.detach().cpu().tolist()},
         "optimizer": optimizer_state(model, opt)}
    s["snapshot_sha256"] = sha(s)
    return s


def reconstruct(raw, snap):
    core = source.Core()
    core.load_state_dict({k: torch.tensor(v, dtype=torch.float32)
                          for k, v in raw["base_state"].items()})
    model = source.Adapted(core)
    with torch.no_grad():
        model.a.copy_(torch.tensor(snap["adapter"]["a"], dtype=torch.float32))
        model.b.copy_(torch.tensor(snap["adapter"]["b"], dtype=torch.float32))
    opt = torch.optim.AdamW([model.a, model.b], lr=source.LR_ADAPTER)
    if snap["optimizer"]["step"]:
        for name, param in (("a", model.a), ("b", model.b)):
            opt.state[param] = {
                "step": torch.tensor(float(snap["optimizer"]["step"])),
                "exp_avg": torch.tensor(snap["optimizer"][f"avg_{name}"], dtype=param.dtype),
                "exp_avg_sq": torch.tensor(snap["optimizer"][f"sq_{name}"], dtype=param.dtype),
            }
    return model, opt


def validate_request_binding(req, cursor, query_id):
    if req.get("cursor") != cursor or req.get("query_id") != query_id:
        raise ValueError("request_binding")


def independent_update(model, opt, x, y):
    model.train()
    features = torch.tensor([x], dtype=torch.float32)
    label = torch.tensor([y], dtype=torch.long)
    for _ in range(source.UPDATES):
        objective = F.cross_entropy(model(features), label)
        opt.zero_grad(set_to_none=True)
        objective.backward()
        opt.step()


def independent_predict(model, xs):
    model.eval()
    with torch.inference_mode():
        z = torch.as_tensor(xs, dtype=torch.float32)
        return model(z).argmax(dim=-1).cpu().tolist()


def validate_report(report, seed, volroot):
    if report["schema"] != "needle-single-query-ack-run-v1" or report["allocation"] != ALLOCATION:
        raise ValueError("run_identity")
    if report["seed"] != seed:
        raise ValueError("run_seed")
    regenerated = source.make_data(seed)
    if report["input"] != regenerated:
        raise ValueError("input_regeneration")
    expected_worker = {k: v for k, v in regenerated.items()
                       if k not in ("x_support", "schedule", "input_sha256")}
    if report["worker_input"] != expected_worker:
        raise ValueError("worker_input_boundary")
    if any(k in report["worker_input"] for k in ("x_support", "schedule", "y_eval", "y_support")):
        raise ValueError("worker_label_or_future_leak")
    expected_qids = [(i * 37 + seed) % len(regenerated["x_eval"])
                     for i in range(source.ARRIVALS)]
    if report["query_ids"] != expected_qids:
        raise ValueError("query_schedule")
    if set(report["arms"]) != set(MODES):
        raise ValueError("arm_set")
    expected_rows = {m: [] for m in MODES}
    for mode in MODES:
        model, opt = reconstruct(regenerated, source.initial(regenerated))
        for cursor, entry in enumerate(regenerated["schedule"][:source.ARRIVALS]):
            row = entry["row"]
            sx = regenerated["x_support"][row]
            sy = int(source.labels(torch.tensor([sx]), flip=True)[0].item())
            qid = expected_qids[cursor]
            req = {"cursor": cursor, "mode": mode, "support_x": sx, "support_y": sy,
                   "query_id": qid, "query_x": regenerated["x_eval"][qid]}
            observed = report["arms"][mode][cursor]
            validate_request_binding(observed["request"], cursor, qid)
            if observed["request"] != req:
                raise ValueError(f"request_binding:{mode}:{cursor}")
            independent_update(model, opt, sx, sy)
            query = independent_predict(model, [req["query_x"]])[0]
            whole = independent_predict(model, regenerated["x_eval"])
            snap = expected_snapshot(seed, regenerated["base_sha256"], cursor + 1, model, opt)
            ack = observed["ack"]
            if ack["event"] != "ACK" or ack["cursor"] != cursor + 1:
                raise ValueError(f"ack_cursor:{mode}:{cursor}")
            if ack["snapshot"] != snap:
                raise ValueError(f"snapshot_or_optimizer:{mode}:{cursor}")
            if ack["query_prediction"] != query or query != whole[qid]:
                raise ValueError(f"single_query_parity:{mode}:{cursor}")
            disk_bytes = (canon(snap) + b"\n")
            expected_disk_sha = hashlib.sha256(disk_bytes).hexdigest()
            if ack["disk_sha256"] != expected_disk_sha:
                raise ValueError(f"ack_disk_digest:{mode}:{cursor}")
            if mode == "INLINE_512":
                if ack.get("full_prediction") != whole:
                    raise ValueError(f"inline_vector:{cursor}")
                if observed["post_ack_audit"] is not None:
                    raise ValueError(f"unexpected_post_ack:{cursor}")
            else:
                post = observed["post_ack_audit"]
                if not post or post.get("event") != "POST_ACK_AUDIT" or post.get("cursor") != cursor + 1:
                    raise ValueError(f"post_ack_event:{cursor}")
                if post.get("full_prediction") != whole:
                    raise ValueError(f"post_ack_vector:{cursor}")
            expected_rows[mode].append({"snapshot": snap, "query": query, "whole": whole})
        final_path = Path(volroot) / str(seed) / mode / "snapshot.json"
        actual_bytes = final_path.read_bytes()
        expected_final = canon(expected_rows[mode][-1]["snapshot"]) + b"\n"
        if actual_bytes != expected_final:
            raise ValueError(f"actual_final_bytes:{mode}")
    for cursor in range(source.ARRIVALS):
        for field in ("snapshot", "query", "whole"):
            if expected_rows[MODES[0]][cursor][field] != expected_rows[MODES[1]][cursor][field]:
                raise ValueError(f"matched_arm_parity:{cursor}:{field}")
    return expected_rows


def corruption_controls(seed):
    base_sha = "b" * 64
    model = source.Adapted(source.Core())
    opt = torch.optim.AdamW([model.a, model.b], lr=source.LR_ADAPTER)
    good = expected_snapshot(seed, base_sha, 0, model, opt)
    controls = {}
    bad = copy.deepcopy(good)
    bad["snapshot_sha256"] = "0" * 64
    controls["digest"] = bad
    for name, change in (("role", lambda s: s.__setitem__("role", "A")),
                         ("seed", lambda s: s.__setitem__("seed", seed + 1)),
                         ("cursor", lambda s: s.__setitem__("cursor", 1))):
        bad = copy.deepcopy(good)
        change(bad)
        bad.pop("snapshot_sha256")
        bad["snapshot_sha256"] = sha(bad)
        controls[name] = bad
    rejected = {}
    for name, candidate in controls.items():
        try:
            source.validate_snapshot(candidate, seed, base_sha, 0)
        except ValueError:
            rejected[name] = True
        else:
            rejected[name] = False
    wrong_request = {"cursor": 1, "query_id": -1}
    try:
        validate_request_binding(wrong_request, 0, 3)
        rejected["request_binding"] = False
    except ValueError:
        rejected["request_binding"] = True
    return rejected


def p95(values):
    return sorted(values)[max(0, math.ceil(.95 * len(values)) - 1)] / 1_000_000


def audit(args):
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    reports = []
    errors = []
    controls = corruption_controls(CONSTRUCTION_SEED)
    if len(controls) != 5 or not all(controls.values()):
        errors.append({"seed": CONSTRUCTION_SEED, "error": "corruption_controls_not_rejected"})
    seeds = (CONSTRUCTION_SEED,) if args.construction_full else FORMAL_SEEDS
    for seed in seeds:
        try:
            obj = json.loads((Path(args.raw) / str(seed) / "run.json").read_text(encoding="utf-8"))
            validate_report(obj, seed, args.volume_root)
            reports.append(obj)
        except Exception as exc:
            errors.append({"seed": seed, "error": f"{type(exc).__name__}:{exc}"})
    summary = []
    for obj in reports:
        stage = {}
        for mode in MODES:
            rows = obj["arms"][mode]
            stage[mode] = {
                "ack_p95_ms": p95([r["ack_elapsed_ns"] for r in rows]),
                "update_p95_ms": p95([r["ack"]["update_ns"] for r in rows]),
                "commit_p95_ms": p95([r["ack"]["commit_ns"] for r in rows]),
                "full_batch_p95_ms": p95([
                    (r["ack"].get("full_prediction_ns") if mode == "INLINE_512"
                     else r["post_ack_audit"]["full_prediction_ns"]) for r in rows]),
            }
            if mode == "ONLINE_QUERY_ONLY":
                stage[mode]["single_query_p95_ms"] = p95([r["ack"]["one_prediction_ns"] for r in rows])
        vals = {m: stage[m]["ack_p95_ms"] for m in MODES}
        summary.append({"seed": obj["seed"], "arm_order": obj["arm_order"],
                        "inline_512": stage["INLINE_512"],
                        "online_query_only": stage["ONLINE_QUERY_ONLY"],
                        "online_query_total_elapsed_ms": obj["arm_total_elapsed_ns"]["ONLINE_QUERY_ONLY"] / 1_000_000,
                        "inline_512_total_elapsed_ms": obj["arm_total_elapsed_ns"]["INLINE_512"] / 1_000_000,
                        "ratio": vals["ONLINE_QUERY_ONLY"] / vals["INLINE_512"]})
    if errors:
        disposition = "CONSTRUCTION_AUDIT_FAIL" if args.construction_full else "FAIL_INTEGRITY"
    elif args.construction_full:
        disposition = "CONSTRUCTION_AUDIT_PASS"
    elif all(x["online_query_ack_p95_ms"] <= 60 and x["ratio"] <= .5 for x in summary):
        disposition = "PASS_QUERY_ACK_PATH_SCOPED"
    else:
        disposition = "HOLD_LATENCY_BUDGET"
    result = {"schema": "needle-single-query-ack-audit-v1", "allocation": ALLOCATION,
              "decision": disposition, "checked_seeds": len(reports),
              "checked_arm_arrivals": len(reports) * 2 * source.ARRIVALS,
              "corruption_controls_rejected": sum(controls.values()),
              "errors": errors, "seeds": summary,
              "scope": "synthetic CPU Needle adapter; local Docker only; no adaptation-quality or task-authority claim"}
    out = Path(args.out) / "AUDIT.json"
    out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"decision": disposition, "errors": len(errors),
                      "checked_seeds": len(reports)}, sort_keys=True), flush=True)
    if errors:
        raise SystemExit(2)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--volume-root", required=True)
    p.add_argument("--construction-full", action="store_true")
    a = p.parse_args()
    audit(a)


if __name__ == "__main__":
    main()
