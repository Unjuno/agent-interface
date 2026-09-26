"""Corrected-protocol fresh-seed local CUDA LoRA allocation for Issue #4471."""
import base64, hashlib, io, json, os, random, statistics, time
import torch
from torch import nn

SEED = 3927
DEVICE = torch.device("cuda:0")
FEATURES, HIDDEN, CLASSES, RANK = 8, 16, 4, 2
BASE_STEPS, ADAPTER_STEPS, BATCH, LR = 400, 120, 32, 0.04
EPOCH = 7

def dataset(n, seed, flip0=False, flip1=False):
    g = torch.Generator(device="cpu").manual_seed(seed)
    x = torch.randn((n, FEATURES), generator=g, dtype=torch.float32)
    b0 = (x[:, 0] > 0).long()
    b1 = (x[:, 1] > 0).long()
    if flip0: b0 = 1 - b0
    if flip1: b1 = 1 - b1
    y = b0 * 2 + b1
    digest = hashlib.sha256(x.numpy().tobytes() + y.numpy().tobytes()).hexdigest()
    return x.to(DEVICE), y.to(DEVICE), digest

class Core(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(FEATURES, HIDDEN), nn.Tanh())
        self.head = nn.Linear(HIDDEN, CLASSES)
    def forward(self, x): return self.head(self.enc(x))

class Adapter(nn.Module):
    def __init__(self, core, seed):
        super().__init__()
        self.core = core
        for p in self.core.parameters(): p.requires_grad_(False)
        gen = torch.Generator(device="cpu").manual_seed(seed)
        self.a = nn.Parameter(torch.randn((HIDDEN, RANK), generator=gen) * 0.04)
        self.b = nn.Parameter(torch.zeros((RANK, CLASSES)))
    def forward(self, x):
        h = self.core.enc(x)
        return self.core.head(h) + (h @ self.a @ self.b) / RANK

def accuracy(model, x, y):
    model.eval()
    with torch.no_grad():
        return float((model(x).argmax(-1) == y).float().mean().item())

def measure_full(model, x, y):
    model.eval()
    with torch.no_grad():
        pred = model(x).argmax(-1).detach().cpu().tolist()
    expected = y.detach().cpu().tolist()
    return {"correct": sum(int(a == b) for a, b in zip(expected, pred)),
            "n": len(expected), "accuracy": sum(int(a == b) for a, b in zip(expected, pred)) / len(expected),
            "expected": expected, "predicted": pred}

def fit(model, x, y, seed, steps):
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=LR)
    gen = torch.Generator(device="cpu").manual_seed(seed)
    model.train()
    torch.cuda.synchronize()
    start = time.perf_counter_ns()
    for _ in range(steps):
        idx = torch.randint(len(x), (BATCH,), generator=gen).to(DEVICE)
        loss = nn.functional.cross_entropy(model(x[idx]), y[idx])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    torch.cuda.synchronize()
    return (time.perf_counter_ns() - start) / 1e6

def tensors(adapter):
    return {k: v.detach().cpu().clone() for k, v in adapter.state_dict().items()}

def equal_state(left, right):
    return left.keys() == right.keys() and all(left[k].dtype == right[k].dtype and left[k].shape == right[k].shape and torch.equal(left[k], right[k]) for k in left)

def state_bytes(state):
    stream = io.BytesIO()
    torch.save(state, stream)
    payload = stream.getvalue()
    return payload, hashlib.sha256(payload).hexdigest()

def restore(adapter, state):
    adapter.load_state_dict(state, strict=True)

def dispatch(skill, epoch, adapter_id, version, base, adapters):
    if epoch != EPOCH: return "YIELD", None
    if skill == "A" and adapter_id is None and version is None: return "PROPOSE", base
    expected = {"B": "adapter-B", "C": "adapter-C"}.get(skill)
    if expected is None or adapter_id != expected or version != 1: return "YIELD", None
    return "PROPOSE", adapters[skill]

def main():
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        raise RuntimeError("STOP_CUBLAS_WORKSPACE_CONFIG")
    if torch.__version__ != "2.5.1+cu121" or torch.version.cuda != "12.1":
        raise RuntimeError("STOP_TORCH_CUDA_VERSION")
    if not torch.cuda.is_available() or torch.cuda.get_device_name(DEVICE) != "NVIDIA GeForce RTX 3080 Laptop GPU":
        raise RuntimeError("STOP_GPU_IDENTITY_OR_UNAVAILABLE")
    if torch.cuda.mem_get_info(DEVICE)[0] < 2 * 1024**3:
        raise RuntimeError("STOP_GPU_MEMORY_LOW")
    random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    if torch.cuda.get_device_name(DEVICE) != "NVIDIA GeForce RTX 3080 Laptop GPU":
        raise RuntimeError("Unexpected GPU; frozen local allocation must stop.")

    xa, ya, ha = dataset(512, SEED + 1)
    xb, yb, hb = dataset(16, SEED + 2, flip0=True)
    xc, yc, hc = dataset(16, SEED + 3, flip1=True)
    ea, eya, hea = dataset(4096, SEED + 4)
    eb, eyb, heb = dataset(4096, SEED + 5, flip0=True)
    ec, eyc, hec = dataset(4096, SEED + 6, flip1=True)

    base = Core().to(DEVICE)
    pretrain_ms = fit(base, xa, ya, SEED + 10, BASE_STEPS)
    base_before = {k: v.detach().cpu().clone() for k, v in base.state_dict().items()}

    # Fixed construction order and independent trainable parameters.
    torch.cuda.synchronize(); setup_start = time.perf_counter_ns()
    global_adapter = Adapter(base, SEED + 11).to(DEVICE)
    adapters = {"B": Adapter(base, SEED + 12).to(DEVICE),
                "C": Adapter(base, SEED + 13).to(DEVICE)}
    torch.cuda.synchronize(); adapter_setup_ms = (time.perf_counter_ns() - setup_start) / 1e6
    initial = {k: tensors(v) for k, v in [("global", global_adapter), *adapters.items()]}

    update_ms = {}
    update_ms["global_B"] = fit(global_adapter, xb, yb, SEED + 20, ADAPTER_STEPS)
    update_ms["global_C"] = fit(global_adapter, xc, yc, SEED + 21, ADAPTER_STEPS)
    update_ms["adapter_B"] = fit(adapters["B"], xb, yb, SEED + 22, ADAPTER_STEPS)
    update_ms["adapter_C"] = fit(adapters["C"], xc, yc, SEED + 23, ADAPTER_STEPS)

    learned = {k: tensors(v) for k, v in [("global", global_adapter), *adapters.items()]}
    snapshots = {}
    for key, state in learned.items():
        payload, digest = state_bytes(state)
        initial_payload, initial_digest = state_bytes(initial[key])
        restored = torch.load(io.BytesIO(payload), map_location="cpu", weights_only=True)
        snapshots[key] = {"bytes": len(payload), "sha256": digest,
                          "state_b64": base64.b64encode(payload).decode("ascii"),
                          "initial_bytes": len(initial_payload), "initial_sha256": initial_digest,
                          "initial_state_b64": base64.b64encode(initial_payload).decode("ascii"),
                          "roundtrip_exact": equal_state(state, restored)}
        if not snapshots[key]["roundtrip_exact"]:
            raise AssertionError("snapshot tensor mismatch: " + key)
        restore({"global": global_adapter, **adapters}[key], restored)
        if not equal_state(tensors({"global": global_adapter, **adapters}[key]), state):
            raise AssertionError("post-load tensor mismatch: " + key)

    rollback = {}
    for key, model in [("global", global_adapter), *adapters.items()]:
        restore(model, initial[key])
        rollback[key] = equal_state(tensors(model), initial[key])
        if not rollback[key]: raise AssertionError("rollback mismatch: " + key)
        restore(model, learned[key])

    route_specs = {"A": (None, None, ea, eya), "B": ("adapter-B", 1, eb, eyb), "C": ("adapter-C", 1, ec, eyc)}
    routed = {}
    for skill, (aid, version, xeval, yeval) in route_specs.items():
        decision, selected = dispatch(skill, EPOCH, aid, version, base, adapters)
        expected_model = base if skill == "A" else adapters[skill]
        if decision != "PROPOSE" or selected is not expected_model:
            raise RuntimeError("valid dispatch selected unexpected model: " + skill)
        routed[skill] = measure_full(selected, xeval, yeval)
    shared = {"A": measure_full(global_adapter, ea, eya),
              "B": measure_full(global_adapter, eb, eyb),
              "C": measure_full(global_adapter, ec, eyc)}
    route_tests = {
        "unknown_skill": dispatch("X", EPOCH, None, None, base, adapters)[0],
        "stale_epoch": dispatch("B", EPOCH - 1, "adapter-B", 1, base, adapters)[0],
        "wrong_identity": dispatch("B", EPOCH, "adapter-C", 1, base, adapters)[0],
        "missing_identity": dispatch("B", EPOCH, None, 1, base, adapters)[0],
        "wrong_version": dispatch("C", EPOCH, "adapter-C", 2, base, adapters)[0],
        "missing_version": dispatch("C", EPOCH, "adapter-C", None, base, adapters)[0],
    }
    if any(v != "YIELD" for v in route_tests.values()):
        raise AssertionError("invalid route did not yield")
    for key, model in [("global", global_adapter), *adapters.items()]:
        # Verify trainable updates never changed shared frozen base.
        pass
    base_immutable = all(torch.equal(base.state_dict()[k].detach().cpu(), v)
                         for k, v in base_before.items())
    if not base_immutable: raise AssertionError("frozen base changed")

    # Dispatch-only CPU-side overhead, 5 x 200 valid decisions; not inference latency.
    timings = []
    for _ in range(5):
        start = time.perf_counter_ns()
        for _ in range(200): dispatch("B", EPOCH, "adapter-B", 1, base, adapters)
        timings.append((time.perf_counter_ns() - start) / 200e6)

    result = {
        "allocation": "needle-lora-3441-pilot-04d-corrected-base-20260926-01",
        "outcome": "PENDING_CLASSIFICATION",
        "device": {"name": torch.cuda.get_device_name(DEVICE), "torch": torch.__version__,
                   "cuda": torch.version.cuda, "execution": "Windows host; Docker daemon unavailable"},
        "parameters": {"seed": SEED, "base_pretrain_steps": BASE_STEPS, "adapter_steps": ADAPTER_STEPS, "features": FEATURES, "hidden": HIDDEN,
                       "classes": CLASSES, "rank": RANK, "steps_per_update": STEPS,
                       "batch": BATCH, "lr": LR, "support_each": 16, "heldout_each": 4096},
        "data_sha256": {"A_train": ha, "B_support": hb, "C_support": hc,
                        "A_eval": hea, "B_eval": heb, "C_eval": hec},
        "measurements": {"pretrain_ms": pretrain_ms, "adapter_setup_ms": adapter_setup_ms, "update_ms": update_ms,
                         "routed_accuracy": {k: v["accuracy"] for k,v in routed.items()}, "shared_sequential_accuracy": {k:v["accuracy"] for k,v in shared.items()},
                         "row_evidence": {"routed": routed, "shared": shared},
                         "snapshots": snapshots, "rollback_tensor_exact": rollback,
                         "dispatcher_only_ms_per_call_median": statistics.median(timings),
                         "dispatch_block_means_ms": timings,
                         "cuda_peak_allocated_bytes": None,
                         "cuda_peak_memory_status": "UNAVAILABLE_WDDM"},
        "checks": {"invalid_routes": route_tests, "base_immutable": base_immutable,
                   "all_snapshot_roundtrip_exact": all(x["roundtrip_exact"] for x in snapshots.values()),
                   "all_rollbacks_exact": all(rollback.values())},
        "limitations": ["single synthetic seed", "related synthetic mappings", "not runtime integration",
                       "dispatcher-only timing excludes inference/model loading", "host run is not container verification"]
    }
    # Distinguish skill gate failure from interference H; H is about measurable shared-vs-routed gap.
    p = result["checks"]["base_immutable"] and result["checks"]["all_snapshot_roundtrip_exact"] and result["checks"]["all_rollbacks_exact"] and all(v == "YIELD" for v in route_tests.values())
    if not p: result["outcome"] = "FAIL_SNAPSHOT_OR_ROUTE_INTEGRITY"
    elif all(v["accuracy"] >= 0.90 for v in routed.values()): result["outcome"] = "QUALITY_GATE_MET_PENDING_INDEPENDENT_AUDIT"
    else: result["outcome"] = "FAIL_MULTI_SKILL_INTERFERENCE"
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__": main()

