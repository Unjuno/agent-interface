"""Frozen #3869 selective Needle covariate-shift experiment."""
import argparse
import hashlib
import json
import math
import os
import random
import statistics
import time
from pathlib import Path

import torch
from torch import nn

SEEDS = (3467, 3468, 3469)
LABELS = ("CONTINUE", "CORRECT", "WATCH")
META = {"intent": "track_target", "scope": "local-servo", "epoch": 7}
N_PER_CLASS = 1024


def balanced_class(label, n, seed):
    g = torch.Generator().manual_seed(seed)
    if label == 0:
        xy = (torch.rand(n, 2, generator=g) - .5) * .08
        velocity = (torch.rand(n, 2, generator=g) - .5) * .08
        confidence = .72 + .28 * torch.rand(n, 1, generator=g)
        visible = torch.ones(n, 1)
    elif label == 1:
        sign = torch.where(torch.rand(n, 1, generator=g) > .5, 1., -1.)
        dx = sign * (.15 + .80 * torch.rand(n, 1, generator=g))
        dy = (torch.rand(n, 1, generator=g) - .5) * 1.6
        xy = torch.cat([dx, dy], 1)
        velocity = (torch.rand(n, 2, generator=g) - .5) * .4
        confidence = .72 + .28 * torch.rand(n, 1, generator=g)
        visible = torch.ones(n, 1)
    else:
        xy = (torch.rand(n, 2, generator=g) - .5) * 2.
        velocity = (torch.rand(n, 2, generator=g) - .5) * .8
        confidence = .72 * torch.rand(n, 1, generator=g)
        visible = torch.randint(0, 2, (n, 1), generator=g).float()
    return torch.cat([xy, velocity, confidence, visible], 1)


def shifted_class(label, n, seed):
    g = torch.Generator().manual_seed(seed)
    if label == 1:
        sign = torch.where(torch.rand(n, 1, generator=g) > .5, 1., -1.)
        dx = sign * (.071 + .078 * torch.rand(n, 1, generator=g))
        dy = (torch.rand(n, 1, generator=g) - .5) * .20
        velocity = (torch.rand(n, 2, generator=g) - .5) * .10
        confidence = .80 + .20 * torch.rand(n, 1, generator=g)
        visible = torch.ones(n, 1)
        return torch.cat([dx, dy, velocity, confidence, visible], 1)
    return balanced_class(label, n, seed)


def teacher(x):
    dx, dy, vx, vy, confidence, visible = x.unbind(-1)
    watch = (confidence < .72) | (visible < .5)
    settled = (dx.abs() < .06) & (dy.abs() < .06) & ((vx.abs() + vy.abs()) < .12)
    return torch.where(watch, 2, torch.where(settled, 0, 1)).long()


class Needle(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(6, 16), nn.Tanh(), nn.Linear(16, 16), nn.Tanh(), nn.Linear(16, 3))

    def forward(self, x):
        return self.net(x)


def proposal(meta, x, model):
    if meta != META:
        return None, "YIELD_METADATA"
    if not torch.isfinite(x).all():
        return None, "YIELD_NONFINITE"
    dx, dy, vx, vy, confidence, visible = x.tolist()
    if max(abs(dx), abs(dy)) > 1.25 or max(abs(vx), abs(vy)) > 1.0 or not 0 <= confidence <= 1 or visible not in (0., 1.):
        return None, "YIELD_ENVELOPE"
    if (abs(confidence - .72) < .03 or abs(abs(dx) - .06) < .01 or abs(abs(dy) - .06) < .01
            or abs(abs(vx) + abs(vy) - .12) < .02):
        return None, "YIELD_BOUNDARY"
    with torch.no_grad():
        return LABELS[int(model(x.unsqueeze(0)).argmax(-1).item())], "PROPOSAL"


def boundary_rows():
    rows = []
    for i in range(256):
        d = .25 + (i % 17) * .001
        rows.extend([[d, .2, .01, .02, .719, 1.], [d, .2, .01, .02, .721, 1.]])
        rows.extend([[.059, 0., .02, .02, .9, 1.], [.061, 0., .02, .02, .9, 1.]])
        rows.extend([[0., 0., .059, .06, .9, 1.], [0., 0., .061, .06, .9, 1.]])
    return torch.tensor(rows, dtype=torch.float32)


def train(seed):
    random.seed(seed)
    torch.manual_seed(seed)
    train_x = torch.cat([balanced_class(c, 2048, seed + 10 + c) for c in range(3)])
    train_y = teacher(train_x)
    model = Needle()
    opt = torch.optim.AdamW(model.parameters(), lr=.008)
    g = torch.Generator().manual_seed(seed + 30)
    model.train()
    started = time.perf_counter_ns()
    for _ in range(700):
        ix = torch.randint(len(train_x), (64,), generator=g)
        loss = nn.functional.cross_entropy(model(train_x[ix]), train_y[ix])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    train_ms = (time.perf_counter_ns() - started) / 1e6
    model.eval()
    return model, train_ms


def evaluate_suite(model, seed, name, shifted):
    rows = []
    for cls in range(3):
        fn = shifted_class if shifted else balanced_class
        x = fn(cls, N_PER_CLASS, seed + (100 if shifted else 200) + cls)
        y = teacher(x)
        for features, target in zip(x, y):
            pred, reason = proposal(META, features, model)
            rows.append({"x": [float(v) for v in features], "y": int(target), "proposal": pred, "reason": reason})
    return {"name": name, "rows": rows}


def percentiles(values):
    vals = sorted(values)
    return {"p50": statistics.median(vals), "p95": vals[int(.95 * (len(vals) - 1))],
            "p99": vals[int(.99 * (len(vals) - 1))], "n": len(vals)}


def run_seed(seed):
    model, train_ms = train(seed)
    iid = evaluate_suite(model, seed, "iid_control", False)
    shifted = evaluate_suite(model, seed, "near_boundary_shift", True)
    boundaries = []
    for x in boundary_rows():
        pred, reason = proposal(META, x, model)
        boundaries.append({"x": [float(v) for v in x], "y": int(teacher(x)), "proposal": pred, "reason": reason})
    latencies = []
    latency_x = balanced_class(1, 2000, seed + 300)
    for x in latency_x:
        t = time.perf_counter_ns()
        proposal(META, x, model)
        latencies.append((time.perf_counter_ns() - t) / 1e6)
    invalid = []
    invalid_cases = [
        ("stale_epoch", META | {"epoch": 8}, torch.tensor([.2, .2, 0., 0., .9, 1.])),
        ("wrong_scope", META | {"scope": "other"}, torch.tensor([.2, .2, 0., 0., .9, 1.])),
        ("wrong_intent", {"intent": "other", "scope": META["scope"], "epoch": META["epoch"]}, torch.tensor([.2, .2, 0., 0., .9, 1.])),
        ("out_of_envelope", META, torch.tensor([1.3, 0., 0., 0., .9, 1.])),
        ("nonfinite", META, torch.tensor([float("nan"), 0., 0., 0., .9, 1.])),
    ]
    for case, m, x in invalid_cases:
        pred, reason = proposal(m, x, model)
        invalid.append({"case": case, "meta": m,
                        "x": ["NaN" if math.isnan(float(v)) else float(v) for v in x],
                        "proposal": pred, "reason": reason})
    state = {name: {"shape": list(param.shape), "values": [float(v) for v in param.detach().cpu().reshape(-1)]}
             for name, param in model.state_dict().items()}
    state_bytes = json.dumps(state, sort_keys=True, separators=(",", ":")).encode()
    return {"seed": seed, "train_ms": train_ms, "model_state": state,
            "model_state_sha256": hashlib.sha256(state_bytes).hexdigest(), "iid_control": iid,
            "near_boundary_shift": shifted, "boundary": boundaries,
            "latency_ms": latencies, "invalid_controls": invalid}


def main():
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    result = {"allocation": "needle-intent-distill-3458-pilot-06-isolated-shift-audit",
              "issue": 3869, "seeds": [run_seed(s) for s in SEEDS],
              "scope": "synthetic authority-neutral proposal only; no execution authority"}
    raw = (json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    (out / "FORMAL_RESULT.json").write_bytes(raw)
    print(json.dumps({"allocation": result["allocation"], "seeds": list(SEEDS),
                      "raw_sha256": hashlib.sha256(raw).hexdigest(), "raw_bytes": len(raw)}, sort_keys=True))


if __name__ == "__main__":
    main()
