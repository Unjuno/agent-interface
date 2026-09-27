"""Deterministic synthetic System-1 backend comparison; no actions are executed."""
import argparse
import json
import math
import random
import time
from pathlib import Path

import torch

LABELS = ("LEFT", "RIGHT", "HOLD", "REACQUIRE", "YIELD", "NO_ACTION")
NAMES = ("dx", "dy", "vx", "vy", "confidence", "obs_age", "intent_track", "intent_settle", "phase", "target_visible", "scope_current", "goal_complete")
FEATS = 12


def oracle(x):
    dx, dy, vx, vy, conf, age, track, settle, phase, visible, scope, done = x
    if done > .5:
        return 5
    if scope < .5:
        return 4
    if visible < .5 or conf < .28 or age > .72:
        return 3
    # A coupled, smooth control surface: braking depends on closing velocity.
    lateral = dx + .42 * vx
    vertical = dy + .42 * vy
    if settle > .5:
        lateral += .22 * vx
        vertical += .22 * vy
    threshold = .13 + .045 * phase
    if abs(lateral) <= threshold and abs(vertical) <= threshold:
        return 2
    if abs(lateral) > abs(vertical):
        return 0 if lateral < 0 else 1
    return 2 if abs(vertical) <= threshold * 1.65 else (0 if vertical < 0 else 1)


def make_row(rng, shifted=False):
    # iid and shifted groups have disjoint deterministic trajectory families.
    scale = 1.65 if shifted else 1.0
    dx = rng.uniform(-scale, scale)
    dy = rng.uniform(-scale, scale)
    vx = rng.uniform(-.95, .95) + (rng.choice((-.7, .7)) if shifted and rng.random() < .22 else 0)
    vy = rng.uniform(-.95, .95) + (rng.choice((-.7, .7)) if shifted and rng.random() < .22 else 0)
    intent = rng.randrange(2)
    phase = rng.random()
    conf = rng.uniform(.55, 1.0)
    age = rng.uniform(0, .35)
    noise = .13 if shifted else .045
    dx += rng.gauss(0, noise)
    dy += rng.gauss(0, noise)
    return [dx, dy, vx, vy, conf, age, float(intent == 0), float(intent == 1), phase, 1., 1., 0.]


def dataset(seed, n, shifted=False):
    rng = random.Random(seed)
    rows = [make_row(rng, shifted) for _ in range(n)]
    return rows, [oracle(x) for x in rows]


def rule(x):
    if x[11] > .5: return 5
    if x[10] < .5: return 4
    if x[9] < .5 or x[4] < .4 or x[5] > .5: return 3
    # Deliberately conservative proportional controller, less predictive than oracle.
    px = x[0] + .12 * x[2]
    py = x[1] + .12 * x[3]
    if abs(px) < .18 and abs(py) < .18: return 2
    if abs(px) > abs(py): return 0 if px < 0 else 1
    return 0 if py < 0 else 1


def fit_tree(xs, ys, depth=4):
    def grow(ids, d):
        counts = [sum(ys[i] == c for i in ids) for c in range(len(LABELS))]
        pred = max(range(len(counts)), key=lambda c: (counts[c], -c))
        node = {"pred": pred}
        if d == depth or len(ids) < 8 or max(counts) == len(ids): return node
        best = None
        parent = 1 - sum((c / len(ids)) ** 2 for c in counts)
        for f in range(FEATS):
            vals = sorted(set(xs[i][f] for i in ids))
            if len(vals) < 2: continue
            cuts = [(a + b) / 2 for a, b in zip(vals, vals[1:])]
            if len(cuts) > 31: cuts = [cuts[k] for k in range(1, len(cuts)-1, max(1, len(cuts)//30))]
            for cut in cuts:
                lo = [i for i in ids if xs[i][f] <= cut]
                hi = [i for i in ids if xs[i][f] > cut]
                if not lo or not hi: continue
                def gini(part):
                    cc = [sum(ys[i] == c for i in part) for c in range(len(LABELS))]
                    return 1 - sum((c / len(part)) ** 2 for c in cc)
                gain = parent - (len(lo)*gini(lo) + len(hi)*gini(hi))/len(ids)
                key = (gain, -f, -cut)
                if best is None or key > best[0]: best = (key, f, cut, lo, hi)
        if best is None or best[0][0] <= 1e-12: return node
        _, f, cut, lo, hi = best
        node.update(feature=f, cut=cut, left=grow(lo, d+1), right=grow(hi, d+1))
        return node
    return grow(list(range(len(xs))), 0)


def tree_predict(t, x):
    while "feature" in t:
        t = t["left"] if x[t["feature"]] <= t["cut"] else t["right"]
    return t["pred"]


def fit_mlp(xs, ys, seed):
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    model = torch.nn.Sequential(torch.nn.Linear(FEATS, 16), torch.nn.Tanh(), torch.nn.Linear(16, 16), torch.nn.Tanh(), torch.nn.Linear(16, len(LABELS)))
    opt = torch.optim.Adam(model.parameters(), lr=.008)
    X = torch.tensor(xs, dtype=torch.float32)
    Y = torch.tensor(ys, dtype=torch.long)
    gen = torch.Generator().manual_seed(seed + 17)
    for _ in range(8):
        order = torch.randperm(len(xs), generator=gen)
        for start in range(0, len(xs), 32):
            ix = order[start:start+32]
            opt.zero_grad(); loss = torch.nn.functional.cross_entropy(model(X[ix]), Y[ix]); loss.backward(); opt.step()
    return {k: v.detach().tolist() for k, v in model.state_dict().items()}


def mlp_predict(state, x):
    # independent pure-Python inference used by evaluator and auditor.
    a = x
    for layer in (0, 2, 4):
        w, b = state[f"{layer}.weight"], state[f"{layer}.bias"]
        z = [sum(w[j][i] * a[i] for i in range(len(a))) + b[j] for j in range(len(w))]
        if layer != 4: z = [math.tanh(v) for v in z]
        a = z
    return max(range(len(a)), key=lambda i: (a[i], -i))


def metrics(xs, ys, preds):
    safe = [i for i, x in enumerate(xs) if x[9] > .5 and x[10] > .5 and x[11] < .5 and x[4] >= .28 and x[5] <= .72]
    return {"coverage": sum(preds[i] == ys[i] for i in safe) / len(safe),
            "actionable_precision": sum(preds[i] == ys[i] for i in safe) / max(1, sum(preds[i] in (0,1,2) for i in safe)),
            "controls_exact": all(preds[i] == ys[i] for i in range(len(xs)) if i not in safe)}


def controls():
    base = [.3, .1, 0., 0., .9, .1, 1., 0., .5, 1., 1., 0.]
    return [base[:9] + [0., 1., 0.], base[:9] + [1., 0., 0.], base[:4] + [.2, .1] + base[6:], base[:11] + [1.]]


def run(seed, out):
    train_x, train_y = dataset(seed, 512)
    iid_x, iid_y = dataset(seed + 100_000, 1024)
    shift_x, shift_y = dataset(seed + 200_000, 1024, shifted=True)
    ctrl_x = controls(); ctrl_y = [oracle(x) for x in ctrl_x]
    tree = fit_tree(train_x, train_y)
    mlp = fit_mlp(train_x, train_y, seed + 31)
    result = {"seed": seed, "n_train": len(train_x), "models": {"tree": tree, "mlp": mlp}, "groups": {}}
    for name, xs, ys in (("iid", iid_x, iid_y), ("shift", shift_x, shift_y), ("controls", ctrl_x, ctrl_y)):
        result["groups"][name] = {"rows": xs, "labels": ys, "predictions": {"rule": [rule(x) for x in xs], "tree": [tree_predict(tree,x) for x in xs], "mlp": [mlp_predict(mlp,x) for x in xs]}}
        result["groups"][name]["metrics"] = {k: metrics(xs, ys, v) for k,v in result["groups"][name]["predictions"].items()}
    # Batched timing: only inference, warmed, 5 x 1024 rows per backend; report p95 row latency.
    timing = {}
    for backend, fn in (("rule",rule),("tree",lambda x:tree_predict(tree,x)),("mlp",lambda x:mlp_predict(mlp,x))):
        samples=[]
        for x in iid_x[:1024]:
            t=time.perf_counter_ns(); fn(x); samples.append(time.perf_counter_ns()-t)
        samples.sort(); timing[backend]={"p50_ns":samples[len(samples)//2],"p95_ns":samples[int(.95*len(samples))-1],"n":len(samples)}
    result["latency"] = timing
    out.write_text(json.dumps(result, separators=(",",":")), encoding="utf-8")


if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--seed",type=int,required=True); p.add_argument("--out",type=Path,required=True); a=p.parse_args(); run(a.seed,a.out)
