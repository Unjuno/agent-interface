"""Online role-adapter update schedule experiment; CPU-only, in-memory."""
import base64, copy, gzip, hashlib, io, json, math, platform, random, statistics, time
import torch
from torch import nn

SEED = 3445
D, H, C, RANK = 8, 16, 4, 2
N_BASE, N_SUPPORT, N_HELDOUT = 512, 16, 4096
BASE_STEPS, ONLINE_STEPS_PER_FEEDBACK = 400, 8
BATCH_STEPS = N_SUPPORT * ONLINE_STEPS_PER_FEEDBACK
LR_BASE, LR_ADAPTER = 0.025, 0.04

def data(n, seed):
    return torch.randn(n, D, generator=torch.Generator(device="cpu").manual_seed(seed))

def labels(x, flip=False):
    a = (x[:, 0] > 0).long()
    if flip:
        a = 1 - a
    b = (x[:, 1] > 0).long()
    return a * 2 + b

class Core(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(D, H), nn.Tanh())
        self.head = nn.Linear(H, C)
    def forward(self, x):
        return self.head(self.enc(x))

class LoRA(nn.Module):
    def __init__(self, core):
        super().__init__()
        self.core = core
        for p in core.parameters():
            p.requires_grad_(False)
        self.a = nn.Parameter(torch.randn(H, RANK) * 0.04)
        self.b = nn.Parameter(torch.zeros(RANK, C))
    def forward(self, x):
        h = self.core.enc(x)
        return self.core.head(h) + (h @ self.a @ self.b) / RANK

def clone_state(model):
    return {k: v.detach().clone() for k, v in model.state_dict().items()}

def exact_state(model, state):
    now = model.state_dict()
    return list(now) == list(state) and all(
        now[k].dtype == state[k].dtype and now[k].shape == state[k].shape
        and torch.equal(now[k], state[k]) for k in state
    )

def fit_base(model, x, y):
    opt = torch.optim.AdamW(model.parameters(), lr=LR_BASE)
    g = torch.Generator(device="cpu").manual_seed(SEED + 10)
    started = time.perf_counter_ns()
    model.train()
    for _ in range(BASE_STEPS):
        ix = torch.randint(len(x), (32,), generator=g)
        loss = nn.functional.cross_entropy(model(x[ix]), y[ix])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    return (time.perf_counter_ns() - started) / 1e6

def update_steps(model, opt, x, y, indices, rng):
    model.train()
    for _ in range(ONLINE_STEPS_PER_FEEDBACK):
        ix = torch.randint(len(indices), (32,), generator=rng)
        index_tensor = torch.as_tensor(indices, dtype=torch.long)
        batch_ix = index_tensor[ix]
        loss = nn.functional.cross_entropy(model(x[batch_ix]), y[batch_ix])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()

def accuracy_rows(model, x, y):
    model.eval()
    with torch.no_grad():
        preds = model(x).argmax(-1)
    return int((preds == y).sum().item()), preds.tolist(), y.tolist()

def dispatch(role, epoch, expected_epoch, version, expected_version, base, registry):
    if epoch != expected_epoch:
        return "YIELD", None
    if role == "A":
        return "PROPOSE", base
    if role not in ("B_ONLINE", "B_BATCH") or version != expected_version:
        return "YIELD", None
    model = registry.get(role)
    return ("PROPOSE", model) if model is not None else ("YIELD", None)

def snapshot_bytes(model):
    buf = io.BytesIO()
    torch.save(clone_state(model), buf)
    return buf.getvalue()

def pct95(xs):
    return sorted(xs)[math.ceil(0.95 * len(xs)) - 1]

def main():
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(SEED)
    torch.manual_seed(SEED)

    xa, xb, ea, eb = [
        data(n, SEED + i) for i, n in enumerate(
            (N_BASE, N_SUPPORT, N_HELDOUT, N_HELDOUT), start=1
        )
    ]
    ya, yb = labels(xa), labels(xb, True)
    eya, eyb = labels(ea), labels(eb, True)

    base = Core()
    base_pretrain_ms = fit_base(base, xa, ya)
    base_state = clone_state(base)
    template = LoRA(base)
    initial = clone_state(template)
    online = LoRA(base)
    batch = LoRA(base)
    online.load_state_dict(initial)
    batch.load_state_dict(initial)

    # Online arm: feedback is revealed one row at a time. Each arrival permits
    # eight optimizer steps over only the support rows seen so far.
    online_opt = torch.optim.AdamW([online.a, online.b], lr=LR_ADAPTER)
    stream_order = torch.randperm(N_SUPPORT, generator=torch.Generator(
        device="cpu").manual_seed(SEED + 20)).tolist()
    seen = []
    feedback_ms = []
    online_trace = []
    rng_online = torch.Generator(device="cpu").manual_seed(SEED + 21)
    for i, row in enumerate(stream_order, start=1):
        seen.append(row)
        started = time.perf_counter_ns()
        update_steps(online, online_opt, xb, yb, seen, rng_online)
        feedback_ms.append((time.perf_counter_ns() - started) / 1e6)
        if i in (1, 2, 4, 8, 12, 16):
            correct, _, _ = accuracy_rows(online, eb, eyb)
            online_trace.append({"feedback_seen": i, "accuracy_n": N_HELDOUT,
                                 "correct": correct, "accuracy": correct / N_HELDOUT})
    online_version = N_SUPPORT

    # Matched batch arm: same initial state, same support rows and 128 updates,
    # but all feedback is available before its first update.
    batch_opt = torch.optim.AdamW([batch.a, batch.b], lr=LR_ADAPTER)
    rng_batch = torch.Generator(device="cpu").manual_seed(SEED + 22)
    started = time.perf_counter_ns()
    all_rows = list(range(N_SUPPORT))
    batch.train()
    for _ in range(BATCH_STEPS):
        ix = torch.randint(N_SUPPORT, (32,), generator=rng_batch)
        loss = nn.functional.cross_entropy(batch(xb[ix]), yb[ix])
        batch_opt.zero_grad(set_to_none=True)
        loss.backward()
        batch_opt.step()
    batch_train_ms = (time.perf_counter_ns() - started) / 1e6

    registry = {"B_ONLINE": online, "B_BATCH": batch}
    route_results = {}
    for role, version, model, x, y in (
        ("A", 16, base, ea, eya),
        ("B_ONLINE", online_version, online, eb, eyb),
        ("B_BATCH", 1, batch, eb, eyb),
    ):
        decision, chosen = dispatch(role, 16, 16, version,
                                    online_version if role == "B_ONLINE" else 1,
                                    base, registry)
        assert decision == "PROPOSE" and chosen is model
        correct, preds, expected = accuracy_rows(chosen, x, y)
        route_results[role] = {"correct": correct, "n": len(expected),
                               "accuracy": correct / len(expected),
                               "expected": expected, "predictions": preds}

    # Every malformed/stale control must refuse without a model proposal.
    controls = {
        "unknown_role": dispatch("B_UNKNOWN", 16, 16, 1, 1, base, registry)[0],
        "stale_epoch": dispatch("B_ONLINE", 15, 16, online_version,
                                online_version, base, registry)[0],
        "wrong_version": dispatch("B_ONLINE", 16, 16, online_version + 1,
                                  online_version, base, registry)[0],
    }
    no_adapter_registry = dict(registry)
    del no_adapter_registry["B_ONLINE"]
    controls["missing_adapter"] = dispatch("B_ONLINE", 16, 16, online_version,
                                           online_version, base,
                                           no_adapter_registry)[0]

    # Full state round-trip and rollback are checked for the online adapter.
    online_initial_bytes = io.BytesIO()
    torch.save(initial, online_initial_bytes)
    initial_payload = online_initial_bytes.getvalue()
    initial_sha = hashlib.sha256(initial_payload).hexdigest()
    learned_state = clone_state(online)
    learned_payload = snapshot_bytes(online)
    learned_sha = hashlib.sha256(learned_payload).hexdigest()
    loaded = torch.load(io.BytesIO(learned_payload), map_location="cpu",
                        weights_only=True)
    online.load_state_dict(loaded)
    roundtrip_exact = exact_state(online, learned_state)
    rollback_state = torch.load(io.BytesIO(initial_payload), map_location="cpu",
                                weights_only=True)
    online.load_state_dict(rollback_state)
    rollback_exact = exact_state(online, initial)
    base_immutable = exact_state(base, base_state)

    result = {
        "allocation": "needle-lora-3441-online-stream-v1",
        "seed": SEED,
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "torch": torch.__version__,
            "device": "cpu",
            "torch_threads": torch.get_num_threads(),
            "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        },
        "frozen_design": {
            "base_pretrain_steps": BASE_STEPS,
            "online_feedback_rows": N_SUPPORT,
            "online_steps_per_feedback": ONLINE_STEPS_PER_FEEDBACK,
            "online_total_steps": N_SUPPORT * ONLINE_STEPS_PER_FEEDBACK,
            "batch_steps": BATCH_STEPS,
            "heldout_per_role": N_HELDOUT,
        },
        "timing_ms": {
            "base_pretrain": base_pretrain_ms,
            "batch_after_feedback": batch_train_ms,
            "online_per_feedback": feedback_ms,
            "online_feedback_p50": statistics.median(feedback_ms),
            "online_feedback_p95": pct95(feedback_ms),
            "online_feedback_max": max(feedback_ms),
            "online_cumulative": sum(feedback_ms),
        },
        "online_learning_curve": online_trace,
        "routed_metrics": route_results,
        "invalid_route_controls": controls,
        "snapshot": {
            "initial_sha256": initial_sha,
            "learned_sha256": learned_sha,
            "initial_bytes": len(initial_payload),
            "learned_bytes": len(learned_payload),
            "full_state_roundtrip_exact": roundtrip_exact,
            "full_state_rollback_exact": rollback_exact,
            "base_immutable": base_immutable,
        },
        "scope": "single synthetic task/seed; host CPU, no container/model-runtime/action-authority claim",
    }
    raw = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    compressed = gzip.compress(raw, mtime=0)
    envelope = {
        "result_sha256": hashlib.sha256(raw).hexdigest(),
        "result_bytes": len(raw),
        "result_gzip_b64": base64.b64encode(compressed).decode(),
        "summary": {
            "online_B_accuracy": route_results["B_ONLINE"]["accuracy"],
            "batch_B_accuracy": route_results["B_BATCH"]["accuracy"],
            "base_A_accuracy": route_results["A"]["accuracy"],
            "online_feedback_p95_ms": result["timing_ms"]["online_feedback_p95"],
            "online_feedback_max_ms": result["timing_ms"]["online_feedback_max"],
            "controls": controls,
            "snapshot": result["snapshot"],
        },
    }
    print(json.dumps(envelope, sort_keys=True, separators=(",", ":")))

if __name__ == "__main__":
    main()
