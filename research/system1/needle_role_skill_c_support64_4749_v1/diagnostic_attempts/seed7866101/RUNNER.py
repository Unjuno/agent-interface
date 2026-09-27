"""One-seed paired diagnostic of role-C support count; not formal evidence."""
import hashlib
import json
import os
import platform
import random
import sys
import time

import torch
from torch import nn

SEED = 7866101
OUT = "/out"
D, H, C, RANK = 8, 16, 4, 2


def data(n, seed):
    return torch.randn(n, D, generator=torch.Generator(device="cpu").manual_seed(seed))


def labels(x, role):
    a, b = (x[:, 0] > 0).long(), (x[:, 1] > 0).long()
    if role == "B":
        a = 1 - a
    if role == "C":
        b = 1 - b
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
        self.a = nn.Parameter(torch.randn(H, RANK) * .04)
        self.b = nn.Parameter(torch.zeros(RANK, C))

    def forward(self, x):
        h = self.core.enc(x)
        return self.core.head(h) + (h @ self.a @ self.b) / RANK


def train(model, x, y, params, steps, lr, seed):
    opt = torch.optim.AdamW(params, lr=lr)
    rng = torch.Generator(device="cpu").manual_seed(seed)
    model.train()
    for _ in range(steps):
        ix = torch.randint(len(x), (32,), generator=rng)
        loss = nn.functional.cross_entropy(model(x[ix]), y[ix])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()


def payload_hash(obj):
    b = json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(b).hexdigest()


def main():
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(SEED)
    torch.manual_seed(SEED)
    xa, xb, xc64, ea, eb, ec = [
        data(n, SEED + i)
        for i, n in enumerate((512, 16, 64, 4096, 4096, 4096), 1)
    ]
    base = Core()
    train(base, xa, labels(xa, "A"), list(base.parameters()), 400, .025, SEED + 10)
    base_before = {k: v.clone() for k, v in base.state_dict().items()}
    template = LoRA(base)
    initial = {k: v.clone() for k, v in template.state_dict().items()}
    bmodel = LoRA(base)
    bmodel.load_state_dict(initial)
    train(bmodel, xb, labels(xb, "B"), [bmodel.a, bmodel.b], 120, .04, SEED + 11)
    arms = {}
    for name, support in (("control16", xc64[:16]), ("treatment64", xc64)):
        model = LoRA(base)
        model.load_state_dict(initial)
        train(model, support, labels(support, "C"), [model.a, model.b], 120, .04, SEED + 12)
        with torch.no_grad():
            pred = model(ec).argmax(-1)
            expected = labels(ec, "C")
            arms[name] = {
                "support_count": int(len(support)),
                "predictions": pred.tolist(),
                "expected": expected.tolist(),
                "correct": int((pred == expected).sum()),
                "total": int(len(expected)),
                "accuracy": float((pred == expected).float().mean()),
                "b_state_sha256": payload_hash({k: v.detach().cpu().tolist() for k, v in bmodel.state_dict().items()}),
                "a_state_sha256": payload_hash({k: v.detach().cpu().tolist() for k, v in base.state_dict().items()}),
            }
    raw = {
        "allocation": "needle-role-c-support64-diagnostic-4749-v1-seed7866101",
        "parent_issue": 4749,
        "diagnostic_only": True,
        "seed": SEED,
        "source_contract": "Issue #4749 support-count construction protocol, independently transcribed; no formal runner or loader invoked",
        "configuration": {"base_examples": 512, "base_steps": 400, "adapter_steps": 120, "batch": 32, "lr_base": .025, "lr_adapter": .04, "heldout_c": 4096, "rng_streams": [1, 2, 3, 4, 5, 6, 10, 11, 12]},
        "pairing": {"support16_is_prefix_of_64": bool(torch.equal(xc64[:16], xc64)), "shared_initialization": True, "same_heldout": True, "A_base_immutable": all(torch.equal(v, base_before[k]) for k, v in base.state_dict().items()), "A_B_hash_equal_across_arms": arms["control16"]["a_state_sha256"] == arms["treatment64"]["a_state_sha256"] and arms["control16"]["b_state_sha256"] == arms["treatment64"]["b_state_sha256"]},
        "arms": arms,
        "delta_treatment_minus_control": arms["treatment64"]["accuracy"] - arms["control16"]["accuracy"],
        "environment": {"python": sys.version, "torch": torch.__version__, "platform": platform.platform(), "device": "cpu", "threads": torch.get_num_threads(), "image_id": "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"},
    }
    raw["raw_payload_sha256"] = payload_hash(raw)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "RAW.json"), "w", encoding="utf-8") as f:
        json.dump(raw, f, sort_keys=True, separators=(",", ":"), allow_nan=False)
    print(json.dumps({k: raw[k] for k in ("allocation", "seed", "delta_treatment_minus_control", "environment", "raw_payload_sha256")}, sort_keys=True))


if __name__ == "__main__":
    main()
