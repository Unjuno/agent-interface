#!/usr/bin/env python3
"""Independent raw-only audit. Does not import candidate.py or run_t0.py."""
import hashlib, json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "raw"

def digest(s): return hashlib.sha256(s.encode()).hexdigest()
def u01(s): return int(digest(s)[:16], 16) / 2**64
def fail(msg):
    print(json.dumps({"status":"FAIL_AUDIT","error":msg}, sort_keys=True)); raise SystemExit(1)

try:
    shallow = json.loads((RAW / "shallow-input.json").read_text())
    bundle = json.loads((RAW / "candidate-output.json").read_text())
except Exception as e: fail(f"raw_read:{e}")
if bundle.get("allocation") != "8914-t0-a02-20261016": fail("allocation_mismatch")
if digest((RAW / "shallow-input.json").read_text()) != bundle.get("shallow_input_sha256"): fail("shallow_hash_mismatch")
if set(shallow) != {"worlds"}: fail("shallow_schema")
if len(bundle.get("attempts", [])) != 103 * 3 * 200: fail("attempt_denominator")
by_world_arm = {}
for row in bundle["attempts"]:
    if set(row) != {"world","arm","cell_id","repeat","sample_key","failure","reset_hash","expected_reset_hash","eligible"}: fail("attempt_schema")
    if not row["eligible"] or row["reset_hash"] != row["expected_reset_hash"]: fail("reset_receipt")
    key = (row["world"], row["arm"], row["cell_id"], row["repeat"])
    if key in by_world_arm: fail("duplicate_attempt_identity")
    by_world_arm[key] = row
    oracle = bundle["oracles"].get(row["world"], {}).get(row["cell_id"])
    if oracle is None: fail("oracle_missing")
    if row["sample_key"] != f"{row['world']}|{row['cell_id']}|deep|{row['repeat']}": fail("repeat_identity_mismatch")
    risk = next((c["risk"] for c in shallow["worlds"][row["world"]]["eligible"] if c["cell_id"] == row["cell_id"]), None)
    if risk is None: fail("cell_not_eligible")
    expected_p = (.06 if row["world"].startswith("null") else
                  (.02 if risk else .22) if row["world"] == "family_shift" else
                  (.22 if risk else .02))
    if oracle["p"] != expected_p: fail("oracle_propensity_mismatch")
    expect_hash = digest(f"reset:{row['world']}:{row['cell_id']}:v1")
    if oracle["reset_hash"] != expect_hash or row["reset_hash"] != expect_hash: fail("reset_hash_invalid")
    expected = u01(f"8915|{row['sample_key']}") < oracle["p"]
    if bool(row["failure"]) != expected: fail("outcome_oracle_mismatch")

# Independently rebuild eligible denominators and arm allocations from shallow rows and scores.
for world, payload in shallow["worlds"].items():
    if set(payload) != {"training","eligible","sentinel_ids","budget"}: fail("world_schema")
    if payload["budget"] != 200: fail("budget_mismatch")
    if any(set(c) != {"cell_id","risk","texture","shallow_trials","shallow_failures"} for c in payload["training"] + payload["eligible"]): fail("shallow_row_schema")
    if any(not c["cell_id"].startswith("train-") for c in payload["training"]): fail("training_family_leakage")
    if any(not c["cell_id"].startswith("eval-") for c in payload["eligible"]): fail("evaluation_family_leakage")
    elig = sorted(c["cell_id"] for c in payload["eligible"])
    if any(c["shallow_trials"] != 2 or c["shallow_failures"] != 0 for c in payload["eligible"]): fail("shallow_zero_contract")
    sent = payload["sentinel_ids"]
    if len(sent) != min(40, len(elig)) or len(set(sent)) != len(sent) or not set(sent) <= set(elig): fail("sentinel_contract")
    rep = int(world.split("-")[-1]) if world.startswith("null-") else 0
    seed_rng = random.Random(8915 + rep * 997 + sum(map(ord, world)))
    expected_sent = sorted(seed_rng.sample(elig, min(40, len(elig))))
    if sent != expected_sent: fail("sentinel_not_reproducible")
    rest = [c for c in elig if c not in set(sent)]
    def rr(ids, n): return [ids[i % len(ids)] for i in range(n)]
    left = 200 - len(sent)
    risk = {c["cell_id"]: c["risk"] for c in payload["eligible"]}
    meta = sorted(rest, key=lambda c: (-risk[c], c))
    feat_scores = bundle["scores"][world]["scores"]
    if set(feat_scores) != set(elig): fail("score_denominator")
    # Reconstruct the declared shallow-only smoother independently.
    from collections import defaultdict
    rates = defaultdict(lambda: [0, 0])
    for cell in payload["training"]:
        for feature in ("risk", "texture"):
            rates[(feature, cell[feature])][0] += cell["shallow_failures"]
            rates[(feature, cell[feature])][1] += cell["shallow_trials"]
    for cell in payload["eligible"]:
        expected_score = sum((rates[(feature, cell[feature])][0] + 1) /
                             (rates[(feature, cell[feature])][1] + 2)
                             for feature in ("risk", "texture")) / 2
        if feat_scores[cell["cell_id"]] != {"feature": expected_score, "metadata": float(cell["risk"])}: fail("score_not_from_shallow_data")
    feat = sorted(rest, key=lambda c: (-feat_scores[c]["feature"], c))
    expected_picks = {"uniform":rr(rest,left),
                      "metadata":rr(meta[:max(1,(len(meta)+1)//2)],left),
                      "feature":rr(feat[:max(1,(len(feat)+1)//2)],left)}
    for arm, extras in expected_picks.items():
        counts = {c: 0 for c in elig}
        for c in sent: counts[c] += 1
        for c in extras: counts[c] += 1
        actual = {c:0 for c in elig}
        for (w,a,c,j), row in by_world_arm.items():
            if w == world and a == arm: actual[c] += 1
        if actual != counts: fail("allocation_reconstruction")

# Aggregate paired null-world discovery lift. Bootstrap worlds, not individual attempts.
null_names = sorted(w for w in shallow["worlds"] if w.startswith("null-"))
per_world = []
for w in null_names:
    counts = {a:0 for a in ("uniform","metadata","feature")}
    for row in bundle["attempts"]:
        if row["world"] == w and row["failure"]: counts[row["arm"]] += 1
    per_world.append((counts["metadata"]-counts["uniform"], counts["feature"]-counts["uniform"]))
rng = random.Random(8915)
boot = []
for _ in range(10000):
    sample = [per_world[rng.randrange(len(per_world))] for _ in per_world]
    boot.append(tuple(sum(v[k] for v in sample)/len(sample)/200 for k in (0,1)))
def ci(k):
    vals=sorted(x[k] for x in boot)
    return [vals[249], vals[9749]]
summary = {}
for arm in ("uniform","metadata","feature"):
    summary[arm] = {}
    for world in ("signal","null","family_shift"):
        rows=[r for r in bundle["attempts"] if r["world"]==world and r["arm"]==arm]
        summary[arm][world]={"attempts":len(rows),"failures":sum(r["failure"] for r in rows),
                             "yield_per_attempt":sum(r["failure"] for r in rows)/len(rows)}
summary["null_feature_minus_uniform_lift_ci_per_attempt"] = ci(1)
summary["null_metadata_minus_uniform_lift_ci_per_attempt"] = ci(0)
lo, hi = ci(1)
if not lo <= 0 <= hi or hi > .05: fail("null_lift_gate")
signal={a:summary[a]["signal"]["failures"] for a in ("uniform","metadata","feature")}
if signal["feature"] <= signal["uniform"]: fail("signal_discovery_gate")
result={"status":"PASS_METHOD_SCOPED","worlds":len(shallow["worlds"]),"attempts":len(bundle["attempts"]),"summary":summary,
        "controls":"structural checks passed; mutation copies not yet evaluated"}
(RAW / "audit.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,sort_keys=True))
