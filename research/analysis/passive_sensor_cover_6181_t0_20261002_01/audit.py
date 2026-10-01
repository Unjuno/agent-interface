#!/usr/bin/env python3
"""Independent raw-only auditor; does not import the candidate module."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

MAIN_SHA = "69a1bf509eb432e5e3c0c294d05ad7671d86adb6"
NO_COVER = "NO_SUFFICIENT_PASSIVE_COVER"


def ids_and_pairs(f):
    states = sorted(f["states"], key=lambda s: s["id"])
    return states, [[a["id"], b["id"]] for a, b in itertools.combinations(states, 2)
                    if a["required_response"] != b["required_response"]]


def trusted_read(ch, state):
    item = ch.get("observations", {}).get(state["id"])
    if not isinstance(item, dict) or item.get("status") != "CURRENT":
        return None
    if item.get("generation") != state.get("expected_generation"):
        return None
    if item.get("value") is None or "value" not in item:
        return None
    return item["value"]


def oracle_cover(f, selected, drop=()):
    chs = {c["id"]: c for c in f["channels"]}
    states, pairs = ids_and_pairs(f)
    by_id = {s["id"]: s for s in states}
    required = sorted(c["id"] for c in f["channels"] if c.get("mandatory"))
    missing = [x for x in required if x not in selected]
    lost = set(drop)
    unresolved = []
    for left, right in pairs:
        witnesses = []
        for name in sorted(selected):
            c = chs[name]
            if c["producer"] in lost:
                continue
            lv, rv = trusted_read(c, by_id[left]), trusted_read(c, by_id[right])
            if lv is not None and rv is not None and lv != rv:
                witnesses.append(name)
        if not witnesses:
            unresolved.append([left, right])
    return {
        "status": "COVER" if not missing and not unresolved else NO_COVER,
        "cost": sum(chs[n]["cost"] for n in selected),
        "channels": sorted(selected),
        "missing_mandatory": missing,
        "unresolved_pairs": unresolved,
    }


def enumerate_oracle(f):
    names = sorted(c["id"] for c in f["channels"])
    rows = []
    for size in range(len(names)+1):
        for combo in itertools.combinations(names, size):
            rows.append(oracle_cover(f, combo))
    covers = [r for r in rows if r["status"] == "COVER"]
    if not covers:
        minimum = {"status": NO_COVER, "channels": [], "cost": None,
                   "minimum_tie_count": 0, "cover_count": 0}
    else:
        win = min(covers, key=lambda r: (r["cost"], len(r["channels"]), r["channels"]))
        ties = [r for r in covers if (r["cost"],len(r["channels"])) ==
                (win["cost"],len(win["channels"]))]
        minimum = {"status":"COVER","channels":win["channels"],"cost":win["cost"],
                   "minimum_tie_count":len(ties),"cover_count":len(covers)}
    return rows, minimum


def oracle_greedy(f):
    chs={c["id"]:c for c in f["channels"]}
    selected=sorted(c["id"] for c in f["channels"] if c.get("mandatory"))
    while True:
        now=oracle_cover(f,selected)
        if now["status"]=="COVER":
            return {"status":"COVER","channels":selected,"cost":now["cost"]}
        left={tuple(p) for p in now["unresolved_pairs"]}
        candidates=[]
        for name,ch in chs.items():
            if name in selected: continue
            after=oracle_cover(f,selected+[name])
            gain=len(left-{tuple(p) for p in after["unresolved_pairs"]})
            if gain: candidates.append((gain/ch["cost"],name))
        if not candidates:
            return {"status":NO_COVER,"channels":selected,"cost":now["cost"]}
        top=max(x[0] for x in candidates)
        selected.append(min(n for score,n in candidates if score==top))
        selected.sort()


def oracle_analysis(f):
    rows, minimum=enumerate_oracle(f)
    all_names=sorted(c["id"] for c in f["channels"])
    selected=minimum["channels"] if minimum["status"]=="COVER" else []
    producers=sorted({next(c["producer"] for c in f["channels"] if c["id"]==x) for x in selected})
    drop={p:oracle_cover(f,selected,drop=[p]) for p in producers}
    full=oracle_cover(f,all_names)
    screenshot=oracle_cover(f,["screenshot"])
    impossible=copy.deepcopy(f)
    by={c["id"]:c for c in impossible["channels"]}
    by["app_status"]["observations"]["S2"]["value"]="effect_uncertain"
    by["app_status"]["observations"]["S3"]["value"]="effect_uncertain"
    _,impossible_min=enumerate_oracle(impossible)
    return {"all_subsets":rows,"minimum":minimum,"greedy":oracle_greedy(f),
            "full_bundle":full,"screenshot_only":screenshot,
            "producer_dropout_from_minimum":drop,
            "impossible_effect_alias":impossible_min,
            "impossible_control_subset_count":len(enumerate_oracle(impossible)[0])}


def claim_is_valid(claim, f):
    selected=claim.get("channels",[])
    raw=oracle_cover(f,selected)
    return claim.get("status")==raw["status"] and raw["status"]=="COVER" and claim.get("cost")==raw["cost"]


def mutation_controls(f, candidate):
    tests={}
    # Mislabel the derived crop as a second independent source.
    m=copy.deepcopy(candidate)
    m["producer_by_channel"]["crop"]="crop_encoder"
    expected={c["id"]:c["producer"] for c in f["channels"]}
    tests["crop_relabel_as_independent"]=(m["producer_by_channel"]!=expected)
    # A missing app state cannot be treated as informative.
    f_missing=copy.deepcopy(f)
    del f_missing["channels"][2]["observations"]["S2"]["value"]
    tests["missing_observation"]=(not claim_is_valid(candidate["analysis"]["minimum"],f_missing))
    # A mismatched generation is stale, not a current distinguishing token.
    f_stale=copy.deepcopy(f)
    f_stale["channels"][2]["observations"]["S2"]["generation"]="g0"
    tests["stale_generation"]=(not claim_is_valid(candidate["analysis"]["minimum"],f_stale))
    # Dispatch is not evidence that the effect occurred.
    f_dispatch=copy.deepcopy(f)
    f_dispatch["channels"][2]["observations"]["S2"]["value"]="dispatch_only"
    tests["dispatch_substituted_for_effect"]=(not claim_is_valid(candidate["analysis"]["minimum"],f_dispatch))
    return {k:{"rejected":bool(v)} for k,v in tests.items()}


def audit(f, candidate, fixture_raw):
    errors=[]
    expected_producers={c["id"]:c["producer"] for c in f["channels"]}
    if candidate.get("schema")!="passive-sensor-cover-candidate-v1": errors.append("schema")
    if candidate.get("main_sha")!=MAIN_SHA: errors.append("main_sha")
    if candidate.get("fixture_sha256")!=hashlib.sha256(fixture_raw).hexdigest(): errors.append("fixture_digest")
    if candidate.get("producer_by_channel")!=expected_producers: errors.append("producer_lineage")
    independent=oracle_analysis(f)
    if candidate.get("analysis")!=independent: errors.append("candidate_oracle_mismatch")
    mutations=mutation_controls(f,candidate)
    if any(not x["rejected"] for x in mutations.values()): errors.append("mutation_accepted")
    if independent["minimum"]!={"status":"COVER","channels":["app_status","os_focus_input"],"cost":7,"minimum_tie_count":1,"cover_count":1}:
        errors.append("preregistered_minimum")
    if independent["greedy"]["cost"]!=8: errors.append("greedy_cost")
    if independent["full_bundle"]["cost"]!=11 or independent["full_bundle"]["status"]!="COVER": errors.append("full_bundle")
    if independent["screenshot_only"]["status"]!=NO_COVER: errors.append("screenshot_only")
    if independent["impossible_effect_alias"]["status"]!=NO_COVER: errors.append("impossible_control")
    if len(independent["all_subsets"])!=16: errors.append("subset_count")
    if any(r["status"]!="NO_SUFFICIENT_PASSIVE_COVER" for r in independent["producer_dropout_from_minimum"].values()):
        errors.append("producer_dropout_not_fail_closed")
    return {"status":"PASS_METHOD_SCOPED" if not errors else "FAIL_RAW_AUDIT",
            "errors":errors,"independent_analysis":independent,
            "mutation_controls":mutations}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("fixture",type=Path)
    p.add_argument("candidate",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    raw=a.fixture.read_bytes()
    f=json.loads(raw)
    candidate=json.loads(a.candidate.read_text(encoding="utf-8"))
    result=audit(f,candidate,raw)
    encoded=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.out: a.out.write_text(encoded,encoding="utf-8")
    else: print(encoded,end="")
    raise SystemExit(0 if result["status"]=="PASS_METHOD_SCOPED" else 1)


if __name__=="__main__":
    main()
