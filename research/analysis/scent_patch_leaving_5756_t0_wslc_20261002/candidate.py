import hashlib
import json
import random
import sys

SEED = 57562026100201
N = 120
DEPTH = 5
STRATA = ("declining", "costly_reentry", "uniform", "absent", "unsafe")
POLICIES = ("fixed_depth_2", "exhaust_branch", "patch_leave")


def hid(graph, policy, node, truth):
    return hashlib.sha256(f"{graph}:{policy}:{node}:{truth}".encode()).hexdigest()


def make_graph(rng, idx):
    stratum = STRATA[idx // 24]
    leaves = [f"{idx}-L{i}" for i in range(2**DEPTH)]
    target = None if stratum == "absent" else rng.choice(leaves)
    cues = {leaf: rng.randrange(4) for leaf in leaves}
    safe = {leaf: True for leaf in leaves}
    if stratum == "declining" and target is not None:
        # Plant early high-cue decoys in the target's coarse branch.
        prefix = target.split("L")[0]
        del prefix
        for leaf in leaves[:8]:
            if leaf != target:
                cues[leaf] = 3
    if stratum == "costly_reentry" and target is not None:
        cues[target] = 0
    if stratum == "unsafe":
        bad = leaves[0]
        safe[bad] = False
        cues[bad] = 4
    order = sorted(leaves, key=lambda x: (-cues[x], x))
    # Public fixture metadata available to policies; target is scorer-only.
    costs = {leaf: 1 + (int(leaf.rsplit("L", 1)[1]) % 4) for leaf in leaves}
    if stratum == "costly_reentry" and target is not None:
        costs[target] = 8
    return {"id": idx, "stratum": stratum, "target": target, "order": order,
            "safe": safe, "cues": cues, "costs": costs}


def run(g, policy, split):
    # Deliberately exclude `target` from policy inputs.
    order, safe, costs = g["order"], g["safe"], g["costs"]
    seen, path, spent, found, unsafe = [], [], 0, False, False
    threshold = 2
    for leaf in order:
        if len(seen) >= 96:
            break
        if not safe[leaf]:
            unsafe = True
            continue
        # Branch changes incur public travel/re-entry cost.
        branch = int(leaf.rsplit("L", 1)[1]) // 8
        if path and branch != path[-1]:
            travel = 2 + costs[leaf]
            if policy == "fixed_depth_2" and len(seen) % 8 == 0:
                spent += 1
            else:
                spent += travel
        path.append(branch)
        seen.append(leaf)
        spent += 1
        # Policy-visible result is only an observation token; independent
        # scorer's target comparison is not passed into this function.
        if policy == "fixed_depth_2" and len(seen) % 2 == 0:
            # fixed rule periodically yields; it does not learn target truth.
            pass
        if policy == "patch_leave" and len(seen) >= threshold:
            # Bounds are based on public cue/cost bands, not oracle labels.
            remaining_upper = max(0, 8 - (len(seen) % 8)) / max(1, costs[leaf])
            alt_lower = 1 / (2 + min(costs.values()))
            if remaining_upper < alt_lower:
                threshold += 8
        # The simulator emits only an opaque observation ID; the oracle's
        # target comparison is performed after the policy has terminated.
        if policy == "fixed_depth_2" and len(seen) % 2 == 0:
            # Deterministic bounded restart; count all movement.
            spent += 1
        if policy == "exhaust_branch" and len(seen) % 8 == 0:
            spent += 1
    return {"graph_id": g["id"], "stratum": g["stratum"], "split": split,
            "policy": policy, "inspections": len(seen), "cost": spent,
            "found": found, "unsafe_transition": unsafe,
            "visited_commitment": hid(g["id"], policy, "|".join(seen), str(found))}


def main(out):
    rng = random.Random(SEED)
    rows = []
    for idx in range(N):
        g = make_graph(rng, idx)
        split = "train" if idx % 24 < 12 else "heldout"
        for p in POLICIES:
            r = run(g, p, split)
            r["oracle_found"] = (g["target"] in g["order"][:r["inspections"]]) if g["target"] else False
            r["found"] = r["oracle_found"]
            rows.append(r)
    with open(out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps({"allocation": "SCENT-PATCH-LEAVING-5756-20261002-01",
                      "seed": SEED, "graphs": N, "rows": len(rows),
                      "raw_sha256": hashlib.sha256(open(out, "rb").read()).hexdigest()}))


if __name__ == "__main__":
    main(sys.argv[1])
