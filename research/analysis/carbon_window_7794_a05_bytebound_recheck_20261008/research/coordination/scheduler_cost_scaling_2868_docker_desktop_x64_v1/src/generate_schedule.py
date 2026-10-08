"""Generate the deterministic all-ready queue schedule used in #5025."""
import json
import random
import sys

SIZES = (8, 32, 128, 512, 2048)
BLOCKS = 15
POLICIES = ("STABLE_LIST_SCAN", "STABLE_SORTED_LIST", "ELIGIBLE_HEAP")
BASE_SEED = 28682026


def make_schedule():
    sizes = {}
    for size in SIZES:
        rng = random.Random(BASE_SEED + size)
        candidates = []
        for seq in range(size):
            candidates.append({
                "priority": rng.randrange(16),
                "deadline": rng.randrange(8),
                "enqueue_seq": seq,
                "op_id": f"op-{seq:05d}",
                "ready": True,
                "expires": None,
            })
        blocks = []
        for block in range(BLOCKS):
            order_rng = random.Random(BASE_SEED + 100000 * size + block)
            order = list(POLICIES)
            order_rng.shuffle(order)
            blocks.append({"block": block, "policy_order": order})
        sizes[str(size)] = {"candidates": candidates, "blocks": blocks}
    return {
        "schema": "scheduler-cost-scaling-docker-desktop-x64-v1",
        "base_seed": BASE_SEED,
        "sizes": list(SIZES),
        "blocks_per_size": BLOCKS,
        "policies": list(POLICIES),
        "key": ["negative_priority", "deadline", "enqueue_seq", "op_id"],
        "all_ready": True,
        "sizes_data": sizes,
    }


if __name__ == "__main__":
    target = sys.argv[1]
    with open(target, "w", encoding="utf-8", newline="\n") as f:
        json.dump(make_schedule(), f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
