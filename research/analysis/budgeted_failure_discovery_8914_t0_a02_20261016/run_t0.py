#!/usr/bin/env python3
"""One-shot deterministic synthetic runner; candidate sees shallow input only."""
import hashlib, json, random, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
SEED = 8915
BUDGET = 200
SENTINELS = 40
ARMS = ("uniform", "metadata", "feature")

def digest(s): return hashlib.sha256(s.encode()).hexdigest()
def u01(s): return int(digest(s)[:16], 16) / 2**64

def p_for(world, risk):
    if world.startswith("null"):
        return .06
    if world == "family_shift":
        return .02 if risk else .22
    return .22 if risk else .02

def make_world(world, rep=0):
    rng = random.Random(SEED + rep * 997 + sum(map(ord, world)))
    training, eligible, oracle = [], [], {}
    for fam_i in range(4):
        fam = f"train-{fam_i}"
        for i in range(40):
            risk, texture = rng.randrange(2), rng.randrange(2)
            cid = f"{fam}-c{i:02d}"
            p = .22 if risk else .02
            fail = sum(u01(f"{SEED}|{world}|{cid}|shallow|{j}") < p for j in range(12))
            training.append({"cell_id": cid, "risk": risk, "texture": texture,
                            "shallow_trials": 12, "shallow_failures": fail})
    for fam_i in range(4):
        fam = f"eval-{fam_i}"
        for i in range(50):
            risk, texture = rng.randrange(2), rng.randrange(2)
            cid = f"{fam}-c{i:02d}"
            p = p_for(world, risk)
            shallow_fail = sum(u01(f"{SEED}|{world}|{cid}|shallow|{j}") < p for j in range(2))
            if shallow_fail == 0:
                eligible.append({"cell_id": cid, "risk": risk, "texture": texture,
                                 "shallow_trials": 2, "shallow_failures": 0})
                oracle[cid] = {"p": p, "reset_hash": digest(f"reset:{world}:{cid}:v1")}
    if len(eligible) < 8:
        raise RuntimeError("insufficient eligible cells")
    eligible.sort(key=lambda c: c["cell_id"])
    sentinel_ids = sorted(rng.sample([c["cell_id"] for c in eligible], min(SENTINELS, len(eligible))))
    return ({"training": training, "eligible": eligible, "sentinel_ids": sentinel_ids,
             "budget": BUDGET}, oracle)


def round_robin(ids, n):
    return [ids[i % len(ids)] for i in range(n)]

# Fixed worlds plus 100 null replicates for the preregistered false-lift interval.
world_names = ["signal", "null", "family_shift"] + [f"null-{i:03d}" for i in range(100)]
shallow = {"worlds": {}}
oracles, world_data = {}, {}
for name in world_names:
    rep = int(name.split("-")[-1]) if name.startswith("null-") else 0
    payload, oracle = make_world(name, rep)
    shallow["worlds"][name] = payload
    oracles[name], world_data[name] = oracle, payload
RAW.mkdir(exist_ok=True)
shallow_path = RAW / "shallow-input.json"
with shallow_path.open("w", encoding="utf-8") as f:
    json.dump(shallow, f, sort_keys=True, separators=(",", ":")); f.write("\n")
score_path = RAW / "candidate-allocation.json"
subprocess.run([sys.executable, str(ROOT / "candidate.py"), str(shallow_path), str(score_path)], check=True)
with score_path.open(encoding="utf-8") as f: scores = json.load(f)

attempts = []
for world in world_names:
    payload, oracle = world_data[world], oracles[world]
    eligible = sorted(c["cell_id"] for c in payload["eligible"])
    sent = payload["sentinel_ids"]
    rest = [c for c in eligible if c not in set(sent)]
    left = BUDGET - len(sent)
    rank_meta = sorted(rest, key=lambda c: (-next(x["risk"] for x in payload["eligible"] if x["cell_id"] == c), c))
    rank_feat = sorted(rest, key=lambda c: (-scores[world]["scores"][c]["feature"], c))
    picks = {"uniform": round_robin(rest, left),
             "metadata": round_robin(rank_meta[:max(1, (len(rank_meta)+1)//2)], left),
             "feature": round_robin(rank_feat[:max(1, (len(rank_feat)+1)//2)], left)}
    for arm in ARMS:
        counts = {c: 0 for c in eligible}
        for c in sent: counts[c] += 1
        for c in picks[arm]: counts[c] += 1
        for cid, n in counts.items():
            for j in range(n):
                key = f"{world}|{cid}|deep|{j}"
                failed = u01(f"{SEED}|{key}") < oracle[cid]["p"]
                attempts.append({"world": world, "arm": arm, "cell_id": cid,
                                 "repeat": j, "sample_key": key, "failure": failed,
                                 "reset_hash": oracle[cid]["reset_hash"],
                                 "expected_reset_hash": oracle[cid]["reset_hash"],
                                 "eligible": True})

bundle = {"allocation": "8914-t0-a02-20261016", "seed": SEED,
          "shallow_input_sha256": digest(shallow_path.read_text()),
          "candidate_sha256": digest((ROOT / "candidate.py").read_text()),
          "attempts": attempts, "oracles": oracles, "scores": scores}
with (RAW / "candidate-output.json").open("w", encoding="utf-8") as f:
    json.dump(bundle, f, sort_keys=True, separators=(",", ":")); f.write("\n")
print(json.dumps({"worlds": len(world_names), "attempts": len(attempts),
                  "eligible_signal_cells": len(world_data["signal"]["eligible"]),
                  "exit": 0}, sort_keys=True))
