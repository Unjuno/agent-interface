#!/usr/bin/env python3
"""Single-allocation resident-vs-respawn online Needle checkpoint study."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import torch
from torch import nn
import torch.nn.functional as F

ALLOCATION = "needle-native-volume-checkpoint-6842731-6842733-6842737-v1"
SEEDS = (6842731, 6842733, 6842737)
CONSTRUCTION_SEED = 6842703
D, H, C = 8, 16, 4
N_BASE, N_SUPPORT, N_HELDOUT = 512, 16, 512
BASE_STEPS, ARRIVALS, UPDATES, BATCH = 400, 12, 8, 32
LR_BASE, LR_ADAPTER = 0.025, 0.04
SCHEMA = "needle-resident-snapshot-v1"


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(x):
    return hashlib.sha256(canonical(x)).hexdigest()


def labels(x, flip=False):
    a = (x[:, 0] > 0).long()
    b = (x[:, 1] > 0).long()
    if flip:
        a = 1 - a
    return a * 2 + b


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
        hidden = self.core.enc(x)
        return self.core.head(hidden) + (hidden @ self.a @ self.b) / 2


def state_dict_list(m):
    return {k: v.detach().cpu().tolist() for k, v in m.state_dict().items()}


def opt_list(m, opt):
    out = {"step": 0}
    for name, p in (("a", m.a), ("b", m.b)):
        s = opt.state.get(p)
        if s is None:
            out[f"avg_{name}"] = torch.zeros_like(p).tolist()
            out[f"sq_{name}"] = torch.zeros_like(p).tolist()
        else:
            out["step"] = int(s["step"].item())
            out[f"avg_{name}"] = s["exp_avg"].detach().cpu().tolist()
            out[f"sq_{name}"] = s["exp_avg_sq"].detach().cpu().tolist()
    return out


def load_opt(m, opt, value):
    if value["step"] == 0:
        return
    for name, p in (("a", m.a), ("b", m.b)):
        opt.state[p] = {
            "step": torch.tensor(float(value["step"])),
            "exp_avg": torch.tensor(value[f"avg_{name}"], dtype=p.dtype),
            "exp_avg_sq": torch.tensor(value[f"sq_{name}"], dtype=p.dtype),
        }


def snapshot(seed, base_sha, cursor, model, opt):
    x = {
        "schema": SCHEMA,
        "allocation": ALLOCATION,
        "seed": seed,
        "role": "B",
        "base_sha256": base_sha,
        "cursor": cursor,
        "adapter": {"a": model.a.detach().cpu().tolist(), "b": model.b.detach().cpu().tolist()},
        "optimizer": opt_list(model, opt),
    }
    x["snapshot_sha256"] = digest(x)
    return x


def validate_snapshot(s, seed, base_sha, cursor):
    z = dict(s)
    claimed = z.pop("snapshot_sha256", None)
    if claimed != digest(z):
        raise ValueError("snapshot_digest")
    if s.get("schema") != SCHEMA or s.get("allocation") != ALLOCATION or s.get("role") != "B":
        raise ValueError("snapshot_schema_or_role")
    if s.get("seed") != seed or s.get("base_sha256") != base_sha or s.get("cursor") != cursor:
        raise ValueError("snapshot_identity_or_cursor")
    if s["optimizer"]["step"] != cursor * UPDATES:
        raise ValueError("snapshot_optimizer_step")


def durable_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    raw = canonical(value) + b"\n"
    with open(tmp, "xb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return hashlib.sha256(raw).hexdigest()


def schedule_for_seed(seed):
    order = torch.randperm(N_SUPPORT, generator=torch.Generator(device="cpu").manual_seed(seed + 21)).tolist()
    rng = torch.Generator(device="cpu").manual_seed(seed + 22)
    seen, schedule = [], []
    for row in order:
        seen.append(row)
        # Eight repeated updates on the newly arrived needle, with no future or
        # prior support examples in this arrival's training batch.
        batches = [[row] for _ in range(UPDATES)]
        schedule.append({"row": row, "seen": list(seen), "batches": batches})
    return order, schedule


def make_data(seed):
    gen = lambda off: torch.Generator(device="cpu").manual_seed(seed + off)
    xb = torch.randn(N_BASE, D, generator=gen(1))
    xs = torch.randn(N_SUPPORT, D, generator=gen(2))
    xe = torch.randn(N_HELDOUT, D, generator=gen(3))
    torch.manual_seed(seed + 10)
    core = Core()
    base_opt = torch.optim.AdamW(core.parameters(), lr=LR_BASE)
    batch_gen = gen(11)
    for _ in range(BASE_STEPS):
        ids = torch.randint(len(xb), (BATCH,), generator=batch_gen)
        loss = F.cross_entropy(core(xb[ids]), labels(xb[ids]))
        base_opt.zero_grad(set_to_none=True)
        loss.backward()
        base_opt.step()
    base = state_dict_list(core)
    base_sha = digest(base)
    order, schedule = schedule_for_seed(seed)
    init_gen = gen(20)
    init = {"a": (torch.randn(H, 2, generator=init_gen) * 0.04).tolist(), "b": torch.zeros(2, C).tolist()}
    result = {
        "schema": "needle-native-volume-input-v1", "allocation": ALLOCATION, "seed": seed,
        # Labels for a support row are revealed only when that row arrives.
        # Held-out labels are deliberately not placed in the trainer input.
        "x_support": xs.tolist(),
        "x_eval": xe.tolist(),
        "base_state": base, "base_sha256": base_sha, "schedule": schedule,
        "initial_adapter": init,
    }
    result["input_sha256"] = digest(result)
    return result


def reconstruct(raw, s):
    core = Core()
    core.load_state_dict({k: torch.tensor(v, dtype=torch.float32) for k, v in raw["base_state"].items()})
    model = Adapted(core)
    with torch.no_grad():
        model.a.copy_(torch.tensor(s["adapter"]["a"], dtype=torch.float32))
        model.b.copy_(torch.tensor(s["adapter"]["b"], dtype=torch.float32))
    opt = torch.optim.AdamW([model.a, model.b], lr=LR_ADAPTER)
    load_opt(model, opt, s["optimizer"])
    return model, opt


def initial(raw):
    core = Core()
    core.load_state_dict({k: torch.tensor(v, dtype=torch.float32) for k, v in raw["base_state"].items()})
    m = Adapted(core)
    with torch.no_grad():
        m.a.copy_(torch.tensor(raw["initial_adapter"]["a"]))
        m.b.copy_(torch.tensor(raw["initial_adapter"]["b"]))
    opt = torch.optim.AdamW([m.a, m.b], lr=LR_ADAPTER)
    return snapshot(raw["seed"], raw["base_sha256"], 0, m, opt)


def update(m, opt, raw, request):
    local_x = torch.tensor([request["x"]], dtype=torch.float32)
    local_y = torch.tensor([request["y"]], dtype=torch.long)
    m.train()
    started = time.perf_counter_ns()
    for _ in range(UPDATES):
        loss = F.cross_entropy(m(local_x), local_y)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    update_ns = time.perf_counter_ns() - started
    m.eval()
    pred_started = time.perf_counter_ns()
    with torch.no_grad():
        pred = m(torch.tensor(raw["x_eval"], dtype=torch.float32)).argmax(-1).tolist()
    prediction_ns = time.perf_counter_ns() - pred_started
    return update_ns, prediction_ns, pred


def process_request(raw, checkpoint, request, state_path):
    cursor = request["cursor"]
    validate_snapshot(checkpoint, raw["seed"], raw["base_sha256"], cursor)
    model, opt = reconstruct(raw, checkpoint)
    update_ns, prediction_ns, pred = update(model, opt, raw, request)
    result_state = snapshot(raw["seed"], raw["base_sha256"], cursor + 1, model, opt)
    t0 = time.perf_counter_ns()
    disk_sha = durable_write(state_path, result_state)
    commit_ns = time.perf_counter_ns() - t0
    return {"cursor": cursor + 1, "snapshot": result_state, "prediction": pred,
            "update_ns": update_ns, "prediction_ns": prediction_ns,
            "commit_ns": commit_ns, "disk_sha256": disk_sha}


def once(args):
    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    checkpoint = json.loads(Path(args.state).read_text(encoding="utf-8"))
    request = json.loads(sys.stdin.readline())
    result = process_request(raw, checkpoint, request, args.state)
    print(json.dumps(result, separators=(",", ":")), flush=True)


def resident(args):
    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    state_path = Path(args.state)
    current = json.loads(state_path.read_text(encoding="utf-8"))
    validate_snapshot(current, raw["seed"], raw["base_sha256"], 0)
    model, opt = reconstruct(raw, current)
    print(json.dumps({"event": "READY", "cursor": 0}), flush=True)
    for line in sys.stdin:
        if not line.strip():
            continue
        req = json.loads(line)
        if req.get("stop"):
            print(json.dumps({"event": "STOPPED", "cursor": current["cursor"]}), flush=True)
            return
        cursor = req["cursor"]
        validate_snapshot(current, raw["seed"], raw["base_sha256"], cursor)
        update_ns, prediction_ns, pred = update(model, opt, raw, req)
        nxt = snapshot(raw["seed"], raw["base_sha256"], cursor + 1, model, opt)
        t0 = time.perf_counter_ns()
        disk_sha = durable_write(state_path, nxt)
        commit_ns = time.perf_counter_ns() - t0
        # Acknowledge only after file and parent directory fsync have completed.
        reread = json.loads(state_path.read_text(encoding="utf-8"))
        validate_snapshot(reread, raw["seed"], raw["base_sha256"], cursor + 1)
        current = reread
        print(json.dumps({"cursor": cursor + 1, "snapshot": current, "prediction": pred,
                          "update_ns": update_ns, "prediction_ns": prediction_ns,
                          "commit_ns": commit_ns,
                          "disk_sha256": disk_sha}, separators=(",", ":")), flush=True)


def ref_run(raw):
    state = initial(raw)
    records = []
    for cursor, entry in enumerate(raw["schedule"]):
        request = {"cursor": cursor, "row": entry["row"],
                   "x": raw["x_support"][entry["row"]],
                   "y": int(labels(torch.tensor([raw["x_support"][entry["row"]]]), flip=True)[0].item())}
        model, opt = reconstruct(raw, state)
        update_ns, prediction_ns, pred = update(model, opt, raw, request)
        state = snapshot(raw["seed"], raw["base_sha256"], cursor + 1, model, opt)
        records.append({"snapshot": state, "prediction": pred, "update_ns": update_ns,
                        "prediction_ns": prediction_ns})
    return records


def run_seed(seed, root, volume_root, arrivals=ARRIVALS):
    raw = make_data(seed)
    d = Path(root) / str(seed)
    d.mkdir(parents=True, exist_ok=False)
    inp = d / "input.json"
    worker_input = {k: v for k, v in raw.items() if k not in ("x_support", "schedule", "input_sha256")}
    durable_write(inp, worker_input)
    reference = ref_run(raw)
    per_arm, startup_by_arm = {}, {}
    order = ["bind", "volume"] if seed in (SEEDS[0], SEEDS[2]) else ["volume", "bind"]
    checkpoint_roots = {"bind": Path(root) / "checkpoints" / str(seed) / "bind",
                        "volume": Path(volume_root) / str(seed) / "volume"}
    for arm in order:
        checkpoint_roots[arm].mkdir(parents=True, exist_ok=False)
        state_path = checkpoint_roots[arm] / "snapshot.json"
        durable_write(state_path, initial(raw))
        arm_rows = []
        worker_started = time.perf_counter_ns()
        proc = subprocess.Popen([sys.executable, "-B", __file__, "--resident", "--input", str(inp),
                                 "--state", str(state_path)], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        ready_line = proc.stdout.readline()
        if not ready_line:
            detail = proc.stderr.read()
            raise RuntimeError(f"{arm}_resident_startup_eof:{detail[-2000:]}")
        ready = json.loads(ready_line)
        if ready != {"event": "READY", "cursor": 0}:
            raise RuntimeError(f"{arm}_resident_not_ready")
        startup_by_arm[arm] = time.perf_counter_ns() - worker_started
        for cursor, entry in enumerate(raw["schedule"][:arrivals]):
            row = entry["row"]
            x = raw["x_support"][row]
            y = int(labels(torch.tensor([x]), flip=True)[0].item())
            req = {"cursor": cursor, "row": row, "x": x, "y": y}
            t0 = time.perf_counter_ns()
            proc.stdin.write(json.dumps(req) + "\n")
            proc.stdin.flush()
            response = json.loads(proc.stdout.readline())
            response_ns = time.perf_counter_ns() - t0
            if response.get("cursor") != cursor + 1:
                raise RuntimeError(f"{arm}_resident_ack_cursor")
            arm_rows.append({"request": req, "response_ns": response_ns, **response})
        proc.stdin.write('{"stop":true}\n')
        proc.stdin.flush()
        stop = json.loads(proc.stdout.readline())
        proc.wait(timeout=30)
        if proc.returncode != 0 or stop != {"event": "STOPPED", "cursor": arrivals}:
            raise RuntimeError(f"{arm}_resident_shutdown")
        per_arm[arm] = arm_rows
    comparisons = []
    for cursor in range(arrivals):
        expected = reference[cursor]
        row = {"cursor": cursor + 1}
        for arm in ("bind", "volume"):
            got = per_arm[arm][cursor]
            row[f"{arm}_snapshot_match"] = got["snapshot"] == expected["snapshot"]
            row[f"{arm}_prediction_match"] = got["prediction"] == expected["prediction"]
        comparisons.append(row)
    result = {"schema": "needle-native-volume-run-v1", "seed": seed, "arrival_count": arrivals, "input": raw,
              "reference": reference, "arms": per_arm, "comparisons": comparisons,
              "arm_order": order, "startup_ns": startup_by_arm, "base_sha256": raw["base_sha256"],
              "checkpoint_paths": {k: str(v / "snapshot.json") for k, v in checkpoint_roots.items()}}
    out = Path(root) / f"seed_{seed}.json"
    durable_write(out, result)
    rank = max(0, __import__("math").ceil(0.95 * arrivals) - 1)
    print(json.dumps({"seed": seed, "arrivals": arrivals, "arm_order": order,
                      **{f"{arm}_p95_ns": sorted(x["response_ns"] for x in per_arm[arm])[rank]
                         for arm in ("bind", "volume")}}, separators=(",", ":")), flush=True)


def formal(args):
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    root = Path(args.out)
    if not args.volume_root:
        raise SystemExit("STOP_VOLUME_ROOT_REQUIRED")
    if not root.is_dir() or any(root.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY_OR_MISSING")
    volume_root = Path(args.volume_root)
    if not volume_root.is_dir() or any(volume_root.iterdir()):
        raise SystemExit("STOP_VOLUME_NOT_EMPTY_OR_MISSING")
    seeds = (CONSTRUCTION_SEED,) if (args.smoke_one or args.construction_full) else SEEDS
    arrivals = 1 if args.smoke_one else ARRIVALS
    for seed in seeds:
        run_seed(seed, root, args.volume_root, arrivals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--formal", action="store_true")
    ap.add_argument("--smoke-one", action="store_true",
                    help="construction-only one seed/arrival; never an eligible allocation")
    ap.add_argument("--construction-full", action="store_true",
                    help="construction-only separate seed/full arrival protocol; never formal")
    ap.add_argument("--worker-once", action="store_true")
    ap.add_argument("--resident", action="store_true")
    ap.add_argument("--input")
    ap.add_argument("--state")
    ap.add_argument("--out")
    ap.add_argument("--volume-root")
    a = ap.parse_args()
    if a.worker_once:
        once(a)
    elif a.resident:
        resident(a)
    elif a.formal or a.smoke_one or a.construction_full:
        formal(a)
    else:
        raise SystemExit("construction-only default; --formal required")


if __name__ == "__main__":
    main()
