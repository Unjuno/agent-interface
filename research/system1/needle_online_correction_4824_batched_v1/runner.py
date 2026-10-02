"""Construction-only fixed-batch successor probe for Issue #4824.

This is not the frozen formal allocation. It uses three distinct construction
seeds and compares the archived one-row/eight-step treatment to one fixed batch
of eight corrections (one optimizer step) after an identical frozen base.
"""
import hashlib
import json
import random
import time
from pathlib import Path

import torch

IMAGE_ID = "sha256:6ab7a93188ddf4232a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
SEEDS = (6811701, 6812701, 6813701)
OUT = Path("/out/construction")
torch.set_num_threads(1)
torch.use_deterministic_algorithms(True)


def data(seed, salt, n):
    rng = random.Random(seed * 1009 + salt)
    first = [0, 1] * (n // 2)
    if salt != 101:
        rng.shuffle(first)
    x = [[bit, *[rng.randrange(2) for _ in range(7)]] for bit in first]
    return torch.tensor(x, dtype=torch.float32), torch.tensor(first, dtype=torch.long)


def digest(ts):
    h = hashlib.sha256()
    for p in ts:
        h.update(bytes(p.detach().contiguous().cpu().view(torch.uint8).flatten().tolist()))
    return h.hexdigest()


def metrics(z, y):
    return {"accuracy": float((z.argmax(1) == y).float().mean()),
            "cross_entropy": float(torch.nn.functional.cross_entropy(z, y)), "n": int(y.numel())}


def route(scope, epoch, current):
    if scope not in ("A", "B") or epoch != current:
        return {"decision": "YIELD", "authority": False, "model_calls": 0}
    return {"decision": "PROPOSAL", "authority": False, "model_calls": 1}


def fit(seed, batched):
    torch.manual_seed(seed)
    sx, _ = data(seed, 101, 16)
    ax, _ = data(seed, 211, 256)
    bx, by = data(seed, 307, 256)
    ay = torch.zeros(256, dtype=torch.long)
    w1 = torch.nn.Parameter(torch.randn(8, 16) * .15)
    b1 = torch.nn.Parameter(torch.zeros(16))
    w2 = torch.nn.Parameter(torch.randn(16, 4) * .15)
    b2 = torch.nn.Parameter(torch.zeros(4))
    base = [w1, b1, w2, b2]
    opt = torch.optim.AdamW(base, lr=.03, weight_decay=1e-4)
    for _ in range(400):
        opt.zero_grad(set_to_none=True)
        torch.nn.functional.cross_entropy(torch.tanh(sx @ w1 + b1) @ w2 + b2,
                                          torch.zeros(16, dtype=torch.long)).backward()
        opt.step()
    for p in base:
        p.requires_grad_(False)
    base_hash = digest(base)
    u = torch.nn.Parameter(torch.randn(16, 2) * .1)
    v = torch.nn.Parameter(torch.zeros(2, 4))
    adapter_opt = torch.optim.AdamW([u, v], lr=.04, weight_decay=1e-4)

    def logits(x):
        h = torch.tanh(x @ w1 + b1)
        return h @ w2 + b2 + (h @ u @ v) / 2

    curves = []
    states = []
    for step in range(9):
        with torch.no_grad():
            za, zb = logits(ax), logits(bx)
            curves.append({"arrival": step, "A": metrics(za, ay), "B": metrics(zb, by),
                           "A_logits": za.tolist(), "B_logits": zb.tolist()})
            states.append({"A": u.detach().tolist(), "B": v.detach().tolist()})
        if step == 8:
            break
        lo = step * 2 if batched else step
        count = 2 if batched else 1
        x = sx[lo:lo+count]
        y = x[:, 0].long()
        adapter_opt.zero_grad(set_to_none=True)
        torch.nn.functional.cross_entropy(logits(x), y).backward()
        adapter_opt.step()
    return {"base_sha256_before": base_hash, "base_sha256_after": digest(base),
            "support": sx.tolist(), "heldout_A": ax.tolist(), "heldout_B": bx.tolist(),
            "heldout_B_y": by.tolist(), "curves": curves, "adapter_states": states,
            "updates": 8 if not batched else 4, "update_batch_size": 1 if not batched else 2,
            "scope": {s: route(s, 7, 7) for s in ("A", "B", "unknown")},
            "stale": route("B", 6, 7)}


def main():
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    OUT.mkdir(parents=True)
    result = {"schema": "needle-online-correction-batched-construction-v1",
              "issue": 4824, "image_id": IMAGE_ID, "torch": torch.__version__,
              "threads": 1, "device": "cpu", "seeds": list(SEEDS),
              "single_row": [fit(s, False) for s in SEEDS],
              "fixed_batch2": [fit(s, True) for s in SEEDS],
              "formal_invocations": 0, "authority": False, "input_emissions": 0}
    raw = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    (OUT / "raw.json").write_text(raw, encoding="utf-8")
    print(json.dumps({"schema": result["schema"], "seeds": len(SEEDS),
                      "single_row_final": [{"A": r["curves"][-1]["A"]["accuracy"], "B": r["curves"][-1]["B"]["accuracy"]} for r in result["single_row"]],
                      "batch2_final": [{"A": r["curves"][-1]["A"]["accuracy"], "B": r["curves"][-1]["B"]["accuracy"]} for r in result["fixed_batch2"]],
                      "formal_invocations": 0}, sort_keys=True))


if __name__ == "__main__":
    main()

