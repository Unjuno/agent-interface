#!/usr/bin/env python3
"""Measure one-query vs inline full-heldout scoring around durable Needle ack.

The frozen #4714 study module is imported read-only from /baseline/study.py.
This file owns only the new timing-placement experiment.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import torch
import torch.nn.functional as F

sys.path.insert(0, "/baseline")
import study as base  # noqa: E402

ALLOCATION = "needle-single-query-ack-6911201-6911301-6911401-v2"
SEEDS = (6911201, 6911301, 6911401)
CONSTRUCTION_SEED = 6911101


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(x):
    return hashlib.sha256(canonical(x)).hexdigest()


def predict(model, xs):
    model.eval()
    with torch.no_grad():
        return model(torch.tensor(xs, dtype=torch.float32)).argmax(-1).tolist()


def update_only(model, opt, x, y):
    model.train()
    xx = torch.tensor([x], dtype=torch.float32)
    yy = torch.tensor([y], dtype=torch.long)
    t0 = time.perf_counter_ns()
    for _ in range(base.UPDATES):
        loss = F.cross_entropy(model(xx), yy)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    return time.perf_counter_ns() - t0


def arm_order_for_seed(seed):
    if seed in (6911201, CONSTRUCTION_SEED, 6911401):
        return ["INLINE_512", "ONLINE_QUERY_ONLY"]
    if seed == 6911301:
        return ["ONLINE_QUERY_ONLY", "INLINE_512"]
    raise ValueError("unallocated_seed")


def worker(args):
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    state_path = Path(args.state)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    model, opt = base.reconstruct(raw, state)
    base.validate_snapshot(state, raw["seed"], raw["base_sha256"], 0)
    print(json.dumps({"event": "READY", "cursor": 0}, separators=(",", ":")), flush=True)
    for line in sys.stdin:
        req = json.loads(line)
        if req.get("stop"):
            print(json.dumps({"event": "STOPPED", "cursor": state["cursor"]}, separators=(",", ":")), flush=True)
            return
        cursor = req["cursor"]
        base.validate_snapshot(state, raw["seed"], raw["base_sha256"], cursor)
        update_ns = update_only(model, opt, req["support_x"], req["support_y"])
        if req["mode"] == "INLINE_512":
            full_started = time.perf_counter_ns()
            full_pred = predict(model, raw["x_eval"])
            full_ns = time.perf_counter_ns() - full_started
            query_pred = full_pred[req["query_id"]]
        elif req["mode"] == "ONLINE_QUERY_ONLY":
            one_started = time.perf_counter_ns()
            query_pred = predict(model, [req["query_x"]])[0]
            one_ns = time.perf_counter_ns() - one_started
            full_pred = None
            full_ns = None
        else:
            raise ValueError("unknown_mode")
        next_state = base.snapshot(raw["seed"], raw["base_sha256"], cursor + 1, model, opt)
        commit_started = time.perf_counter_ns()
        disk_sha = base.durable_write(state_path, next_state)
        commit_ns = time.perf_counter_ns() - commit_started
        reread = json.loads(state_path.read_text(encoding="utf-8"))
        base.validate_snapshot(reread, raw["seed"], raw["base_sha256"], cursor + 1)
        state = reread
        ack = {"event": "ACK", "cursor": cursor + 1, "snapshot": state,
               "query_prediction": query_pred, "update_ns": update_ns,
               "commit_ns": commit_ns, "disk_sha256": disk_sha}
        if req["mode"] == "INLINE_512":
            ack.update({"full_prediction": full_pred, "full_prediction_ns": full_ns})
        else:
            ack["one_prediction_ns"] = one_ns
        print(json.dumps(ack, separators=(",", ":")), flush=True)
        if req["mode"] == "ONLINE_QUERY_ONLY":
            # Hold the post-ack batch until the supervisor has received and
            # parsed ACK; otherwise it can contend with that timed read on the
            # shared one-CPU container.
            receipt = json.loads(sys.stdin.readline())
            if receipt != {"event": "ACK_RECEIVED", "cursor": cursor + 1}:
                raise ValueError("missing_ack_receipt")
            audit_started = time.perf_counter_ns()
            post_pred = predict(model, raw["x_eval"])
            post_ns = time.perf_counter_ns() - audit_started
            print(json.dumps({"event": "POST_ACK_AUDIT", "cursor": cursor + 1,
                              "full_prediction": post_pred, "full_prediction_ns": post_ns},
                             separators=(",", ":")), flush=True)


def run_seed(seed, out_root, volume_root, construction=False):
    raw = base.make_data(seed)
    seed_root = Path(out_root) / str(seed)
    seed_root.mkdir(parents=True, exist_ok=False)
    worker_input = {k: v for k, v in raw.items()
                    if k not in ("x_support", "schedule", "input_sha256")}
    inp = seed_root / "worker-input.json"
    base.durable_write(inp, worker_input)
    query_ids = [(i * 37 + seed) % len(raw["x_eval"]) for i in range(base.ARRIVALS)]
    arm_order = arm_order_for_seed(seed)
    arms = {}
    arm_total_elapsed_ns = {}
    for mode in arm_order:
        state_dir = Path(volume_root) / str(seed) / mode
        state_dir.mkdir(parents=True, exist_ok=False)
        state_path = state_dir / "snapshot.json"
        base.durable_write(state_path, base.initial(raw))
        proc = subprocess.Popen([sys.executable, "-B", __file__, "--worker", "--input", str(inp),
                                 "--state", str(state_path)], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        ready_line = proc.stdout.readline()
        if not ready_line or json.loads(ready_line) != {"event": "READY", "cursor": 0}:
            raise RuntimeError("worker_not_ready:" + proc.stderr.read()[-2000:])
        rows = []
        arm_started = time.perf_counter_ns()
        for cursor, entry in enumerate(raw["schedule"][:base.ARRIVALS]):
            row = entry["row"]
            sx = raw["x_support"][row]
            sy = int(base.labels(torch.tensor([sx]), flip=True)[0].item())
            qid = query_ids[cursor]
            req = {"cursor": cursor, "mode": mode, "support_x": sx, "support_y": sy,
                   "query_id": qid, "query_x": raw["x_eval"][qid]}
            t0 = time.perf_counter_ns()
            proc.stdin.write(json.dumps(req, separators=(",", ":")) + "\n")
            proc.stdin.flush()
            ack = json.loads(proc.stdout.readline())
            ack_ns = time.perf_counter_ns() - t0
            if ack.get("event") != "ACK" or ack.get("cursor") != cursor + 1:
                raise RuntimeError("invalid_ack")
            post = None
            if mode == "ONLINE_QUERY_ONLY":
                proc.stdin.write(json.dumps({"event": "ACK_RECEIVED", "cursor": cursor + 1}) + "\n")
                proc.stdin.flush()
                post = json.loads(proc.stdout.readline())
                if post.get("event") != "POST_ACK_AUDIT" or post.get("cursor") != cursor + 1:
                    raise RuntimeError("missing_post_ack_audit")
            rows.append({"request": req, "ack": ack, "ack_elapsed_ns": ack_ns,
                         "post_ack_audit": post})
        proc.stdin.write('{"stop":true}\n')
        proc.stdin.flush()
        stopped = json.loads(proc.stdout.readline())
        proc.wait(timeout=30)
        if proc.returncode != 0 or stopped != {"event": "STOPPED", "cursor": base.ARRIVALS}:
            raise RuntimeError("worker_shutdown_failed")
        arms[mode] = rows
        arm_total_elapsed_ns[mode] = time.perf_counter_ns() - arm_started
    report = {"schema": "needle-single-query-ack-run-v1", "allocation": ALLOCATION,
              "seed": seed, "construction_only": construction, "input": raw,
              "worker_input": worker_input, "query_ids": query_ids,
              "arm_order": arm_order, "arm_total_elapsed_ns": arm_total_elapsed_ns, "arms": arms,
              "volume_paths": {m: str(Path(volume_root) / str(seed) / m / "snapshot.json")
                               for m in arms}}
    out = seed_root / "run.json"
    base.durable_write(out, report)
    ack_summary = {m: [r["ack_elapsed_ns"] for r in arms[m]] for m in arms}
    p95_index = max(0, __import__("math").ceil(.95 * base.ARRIVALS) - 1)
    print(json.dumps({"seed": seed, "construction_only": construction,
                      **{m.lower() + "_ack_p95_ns": sorted(v)[p95_index]
                         for m, v in ack_summary.items()}}, separators=(",", ":")), flush=True)


def orchestrate(args):
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    out = Path(args.out)
    vol = Path(args.volume_root)
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY_OR_MISSING")
    if not vol.is_dir() or any(vol.iterdir()):
        raise SystemExit("STOP_VOLUME_NOT_EMPTY_OR_MISSING")
    seeds = (CONSTRUCTION_SEED,) if args.construction_full else SEEDS
    for seed in seeds:
        run_seed(seed, out, args.volume_root, args.construction_full)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--orchestrate", action="store_true")
    p.add_argument("--construction-full", action="store_true")
    p.add_argument("--worker", action="store_true")
    p.add_argument("--input")
    p.add_argument("--state")
    p.add_argument("--out")
    p.add_argument("--volume-root")
    a = p.parse_args()
    if a.worker:
        worker(a)
    elif a.orchestrate or a.construction_full:
        orchestrate(a)
    else:
        raise SystemExit("explicit --orchestrate required")


if __name__ == "__main__":
    main()
