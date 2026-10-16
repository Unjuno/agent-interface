#!/usr/bin/env python3
"""Independent raw-only endpoint and factorial-cell auditor for Issue #8544 T0."""
import argparse
import copy
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def score(response, present):
    if not isinstance(response, dict) or set(response) != {"status", "identity", "point", "schema_valid"}:
        return "schema_error"
    if response["schema_valid"] is not True:
        return "schema_error"
    status, identity, point = response["status"], response["identity"], response["point"]
    if status == "abstain" and identity is None and point is None:
        return "abstention"
    if status == "not_found" and identity is None and point is None:
        return "miss" if present else "correct_rejection"
    if status != "found":
        return "ambiguous_identity"
    if not isinstance(point, list) or len(point) != 2 or any(type(x) is not int for x in point):
        return "schema_error"
    if identity == "target" and 480 <= point[0] <= 560 and 340 <= point[1] <= 420:
        return "correct_binding" if present else "false_alarm"
    if identity == "neighbor" and 570 <= point[0] <= 650 and 340 <= point[1] <= 420:
        return "neighbor_substitution" if present else "false_alarm"
    if identity in ("target_or_neighbor", "phantom_target"):
        return "ambiguous_identity" if identity == "target_or_neighbor" else "false_alarm"
    return "false_alarm" if not present else "schema_error"


def expected_ids(spec):
    f = spec["factors"]
    classes = spec["planted_endpoint_classes_by_presence"]
    result = set()
    axes = (f["target_present"], f["spacing_px"], f["eccentricity_proxy_px"], f["target_size_px"], f["flanker_similarity"], f["placement"], f["seeds"])
    for present, spacing, ecc, size, sim, placement, seed in itertools.product(*axes):
        for endpoint in classes["present" if present else "absent"]:
            result.add(f"p{int(present)}-s{spacing}-e{ecc}-z{size}-{sim}-{placement}-seed{seed}-{endpoint}")
    return result


def check(raw, spec):
    if raw.get("schema") != "issue-8544-candidate-raw-v1" or raw.get("authority") != "NONE":
        raise ValueError("schema or authority")
    rows = raw.get("rows", [])
    ids = [r.get("fixture_id") for r in rows]
    if len(ids) != len(set(ids)) or set(ids) != expected_ids(spec):
        raise ValueError("fixture identity/denominator")
    f = spec["factors"]
    cell_counts = Counter()
    endpoint_counts = Counter()
    split_seeds = {"development": set(), "held_out": set()}
    for row in rows:
        if row.get("global_control_count") != f["global_control_count"]:
            raise ValueError("global screen density control")
        expected_split = "held_out" if row.get("seed") in f["held_out_seeds"] else "development"
        if row.get("split") != expected_split:
            raise ValueError("split leakage")
        seed = row.get("seed")
        split_seeds[row["split"]].add(seed)
        outcome = score(row.get("response"), row.get("target_present"))
        if outcome != row.get("planted_endpoint_class"):
            raise ValueError(f"endpoint misclassification {row.get('fixture_id')}: {outcome}")
        cell = (row["target_present"], row["spacing_px"], row["eccentricity_proxy_px"], row["target_size_px"], row["flanker_similarity"], row["placement"], row["planted_endpoint_class"])
        cell_counts[cell] += 1
        endpoint_counts[(row["target_present"], outcome)] += 1
    expected_seed_set = set(f["seeds"])
    if split_seeds["development"] & split_seeds["held_out"] or split_seeds["development"] | split_seeds["held_out"] != expected_seed_set:
        raise ValueError("seed split isolation")
    if any(n != len(f["seeds"]) for n in cell_counts.values()):
        raise ValueError("paired cell seed balance")
    # A complete factorial crossing and constant global item count prevent spacing/eccentricity from aliasing density.
    strata = {(r["spacing_px"], r["eccentricity_proxy_px"], r["target_size_px"], r["flanker_similarity"], r["placement"], r["target_present"]) for r in rows}
    expected_strata = len(f["spacing_px"])*len(f["eccentricity_proxy_px"])*len(f["target_size_px"])*len(f["flanker_similarity"])*len(f["placement"])*len(f["target_present"])
    if len(strata) != expected_strata:
        raise ValueError("factor crossing")
    return {"fixtures":len(rows),"factor_strata":len(strata),"endpoint_cells":len(cell_counts),"split_seeds":{k:sorted(v) for k,v in split_seeds.items()},"checks":len(rows)+len(cell_counts)+5,"errors":0}


def mutation_rejected(raw, spec, kind):
    changed = copy.deepcopy(raw)
    if kind == "drop_fixture": changed["rows"].pop()
    elif kind == "leak_seed": changed["rows"][0]["split"] = "held_out" if changed["rows"][0]["split"] == "development" else "development"
    elif kind == "confound_density": changed["rows"][0]["global_control_count"] += 1
    elif kind == "wrong_identity": changed["rows"][0]["response"]["identity"] = "neighbor"
    elif kind == "wrong_presence_class": changed["rows"][0]["target_present"] = not changed["rows"][0]["target_present"]
    elif kind == "authority_inflation": changed["authority"] = "ACTION_ALLOWED"
    else: raise ValueError("unknown mutation")
    try: check(changed, spec)
    except (ValueError, KeyError, TypeError): return True
    return False


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--spec",default=str(ROOT/"spec.json")); ap.add_argument("--raw",default=str(ROOT/"results/candidate.raw.json")); ap.add_argument("--output",default=str(ROOT/"results/audit.raw.json")); args=ap.parse_args()
    out=Path(args.output)
    if out.exists(): raise SystemExit("refusing existing formal output")
    spec=json.loads(Path(args.spec).read_text()); raw_bytes=Path(args.raw).read_bytes(); raw=json.loads(raw_bytes)
    summary=check(raw,spec)
    controls={k:mutation_rejected(raw,spec,k) for k in ("drop_fixture","leak_seed","confound_density","wrong_identity","wrong_presence_class","authority_inflation")}
    if not all(controls.values()): raise ValueError("mutation control accepted")
    summary.update({"allocation":spec["allocation"],"disposition":"PASS_METHOD_SCOPED","mutation_controls":controls,"mutation_rejections":f"{sum(controls.values())}/{len(controls)}","candidate_raw_sha256":hashlib.sha256(raw_bytes).hexdigest(),"authority":"NONE"})
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(summary,sort_keys=True,separators=(",",":"))+"\n"); print(json.dumps(summary,sort_keys=True))


if __name__ == "__main__": main()
