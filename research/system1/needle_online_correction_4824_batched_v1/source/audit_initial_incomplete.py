"""Independent raw-only auditor for fixed-batch construction probe."""
import hashlib
import json
import random
import sys

import torch

SEEDS = (6811701, 6812701, 6813701)
IMAGE = "sha256:6ab7a93188ddf4232a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"


def rows(seed, salt, n):
    r = random.Random(seed * 1009 + salt)
    f = [0, 1] * (n // 2)
    if salt != 101:
        r.shuffle(f)
    return [[b, *[r.randrange(2) for _ in range(7)]] for b in f]


def fail(msg):
    raise SystemExit("STOP_AUDIT:" + msg)


def audit_arm(seed, obj, batched):
    x_support = rows(seed, 101, 16)
    x_a = rows(seed, 211, 256)
    x_b = rows(seed, 307, 256)
    if obj["support"] != x_support or obj["heldout_A"] != x_a or obj["heldout_B"] != x_b:
        fail(f"data_{seed}_{batched}")
    if obj["base_sha256_before"] != obj["base_sha256_after"]:
        fail(f"base_{seed}_{batched}")
    if len(obj["curves"]) != 9 or len(obj["adapter_states"]) != 9:
        fail(f"curve_count_{seed}_{batched}")
    for i, c in enumerate(obj["curves"]):
        if c["arrival"] != i:
            fail(f"step_{seed}_{batched}_{i}")
        for role in ("A", "B"):
            z = torch.tensor(c[role + "_logits"], dtype=torch.float32)
            y = torch.zeros(256, dtype=torch.long) if role == "A" else torch.tensor([r[0] for r in x_b], dtype=torch.long)
            acc = float((z.argmax(1) == y).float().mean())
            loss = float(torch.nn.functional.cross_entropy(z, y))
            m = c[role]
            if m["n"] != 256 or abs(m["accuracy"] - acc) > 1e-7 or abs(m["cross_entropy"] - loss) > 1e-6:
                fail(f"metric_{seed}_{batched}_{i}_{role}")
    if obj["scope"]["unknown"]["decision"] != "YIELD" or obj["scope"]["unknown"]["model_calls"] != 0:
        fail(f"unknown_scope_{seed}_{batched}")
    if obj["stale"]["decision"] != "YIELD" or obj["stale"]["model_calls"] != 0:
        fail(f"stale_{seed}_{batched}")


def main(path):
    raw = json.load(open(path, encoding="utf-8"))
    if raw.get("schema") != "needle-online-correction-batched-construction-v1" or raw.get("issue") != 4824:
        fail("identity")
    if raw.get("image_id") != IMAGE or raw.get("seeds") != list(SEEDS) or raw.get("formal_invocations") != 0:
        fail("allocation")
    if raw.get("authority") is not False or raw.get("input_emissions") != 0:
        fail("authority")
    for i, seed in enumerate(SEEDS):
        audit_arm(seed, raw["single_row"][i], False)
        audit_arm(seed, raw["fixed_batch2"][i], True)
        if raw["single_row"][i]["updates"] != 8 or raw["fixed_batch2"][i]["updates"] != 4:
            fail(f"update_count_{seed}")
    out = {"decision": "PASS_CONSTRUCTION_AUDIT", "seeds": list(SEEDS),
           "arms": 6, "curves": 54, "recomputed_metric_cells": 108,
           "errors": [], "formal_invocations": 0,
           "scope": "construction only; fixed synthetic support-count/cadence boundary"}
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1])

