from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path


def decode_region(s: str) -> bytes:
    b = base64.b64decode(s, validate=True)
    if len(b) != 32:
        raise ValueError("region_shape")
    return b


def recompute_scores(row: dict) -> list[int]:
    before = [decode_region(s) for s in row["before_b64"]]
    after = [decode_region(s) for s in row["after_b64"]]
    if len(before) != 4 or len(after) != 4:
        raise ValueError("region_count")
    return [sum(abs(x-y) for x, y in zip(b, a)) for b, a in zip(before, after)]


def audit_obj(raw: dict) -> dict:
    errors: list[str] = []
    rows = raw.get("rows")
    if not isinstance(rows, list):
        return {"errors": ["rows_type"]}
    if len(rows) != 48:
        errors.append(f"row_count:{len(rows)}")
    ids = [r.get("case_id") for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_case_id")
    if raw.get("formal_invocations") != 1 or raw.get("reruns") != 0 or raw.get("replacements") != 0 or raw.get("tuning") != 0:
        errors.append("allocation_accounting")

    fam_counts = {"UNIQUE_TRUE":0,"TWO_WAY_TIE":0,"THREE_WAY_TIE":0}
    top1_tie_misses = 0
    candidate_misses = 0
    candidate_nonmax = 0
    unique_singleton_ok = 0
    tie_cardinality_ok = 0
    authority_true = 0

    for idx, row in enumerate(rows):
        if row.get("index") != idx:
            errors.append(f"index:{idx}")
        fam = row.get("family")
        if fam not in fam_counts:
            errors.append(f"family:{idx}")
            continue
        fam_counts[fam] += 1
        truth = row.get("true_region")
        if type(truth) is not int or truth not in range(4):
            errors.append(f"truth:{idx}")
            continue
        try:
            scores = recompute_scores(row)
        except Exception as e:
            errors.append(f"raw:{idx}:{type(e).__name__}")
            continue
        mx = max(scores)
        exact = [i for i,s in enumerate(scores) if s == mx]
        top = [min(exact)]
        for arm_name, expected in (("top1_hard", top), ("exact_max_set", exact)):
            arm = row.get(arm_name)
            if not isinstance(arm, dict):
                errors.append(f"arm:{idx}:{arm_name}")
                continue
            if arm.get("scores") != scores:
                errors.append(f"scores:{idx}:{arm_name}")
            if arm.get("selected_regions") != expected:
                errors.append(f"selected:{idx}:{arm_name}")
            if arm.get("grants_input_authority") is not False:
                errors.append(f"authority:{idx}:{arm_name}")
                authority_true += 1
        cand = row.get("exact_max_set", {})
        top_arm = row.get("top1_hard", {})
        selected = cand.get("selected_regions", [])
        if truth not in selected:
            candidate_misses += 1
        candidate_nonmax += sum(i not in exact for i in selected if type(i) is int)
        expected_exclusive = len(exact) == 1
        if cand.get("exclusive") is not expected_exclusive:
            errors.append(f"exclusive:{idx}")
        if fam == "UNIQUE_TRUE":
            if selected == [truth] and cand.get("exclusive") is True:
                unique_singleton_ok += 1
        else:
            if truth not in top_arm.get("selected_regions", []):
                top1_tie_misses += 1
            expected_card = 2 if fam == "TWO_WAY_TIE" else 3
            if len(selected) == expected_card and cand.get("exclusive") is False:
                tie_cardinality_ok += 1

    if fam_counts != {"UNIQUE_TRUE":12,"TWO_WAY_TIE":24,"THREE_WAY_TIE":12}:
        errors.append(f"family_counts:{fam_counts}")
    if top1_tie_misses != 21:
        errors.append(f"top1_tie_misses:{top1_tie_misses}")
    if candidate_misses != 0:
        errors.append(f"candidate_misses:{candidate_misses}")
    if candidate_nonmax != 0:
        errors.append(f"candidate_nonmax:{candidate_nonmax}")
    if unique_singleton_ok != 12:
        errors.append(f"unique_singleton:{unique_singleton_ok}")
    if tie_cardinality_ok != 36:
        errors.append(f"tie_cardinality:{tie_cardinality_ok}")
    if authority_true != 0:
        errors.append(f"authority_true:{authority_true}")

    return {
        "errors": errors,
        "counts": {
            "rows": len(rows),
            "family_counts": fam_counts,
            "top1_tie_misses": top1_tie_misses,
            "candidate_misses": candidate_misses,
            "candidate_nonmax": candidate_nonmax,
            "unique_singleton_ok": unique_singleton_ok,
            "tie_cardinality_ok": tie_cardinality_ok,
            "authority_true": authority_true,
        },
    }


def mutated(raw: dict, kind: str) -> dict:
    x = copy.deepcopy(raw)
    if kind == "omit_candidate":
        x["rows"][12]["exact_max_set"]["selected_regions"] = [x["rows"][12]["true_region"]]
    elif kind == "extra_nonmax":
        row=x["rows"][0]; scores=recompute_scores(row); low=min(range(4),key=lambda i:scores[i]); row["exact_max_set"]["selected_regions"].append(low)
    elif kind == "wrong_top1":
        x["rows"][12]["top1_hard"]["selected_regions"] = [3]
    elif kind == "truth_out_of_range":
        x["rows"][1]["true_region"] = 9
    elif kind == "raw_byte":
        b=bytearray(decode_region(x["rows"][2]["after_b64"][0])); b[0]^=7; x["rows"][2]["after_b64"][0]=base64.b64encode(bytes(b)).decode()
    elif kind == "duplicate_id":
        x["rows"][3]["case_id"] = x["rows"][2]["case_id"]
    elif kind == "missing_row":
        x["rows"].pop()
    elif kind == "authority_true":
        x["rows"][4]["exact_max_set"]["grants_input_authority"] = True
    elif kind == "score_tamper":
        x["rows"][5]["exact_max_set"]["scores"][0] += 1
    else:
        raise ValueError(kind)
    return x


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("--controls", action="store_true")
    ns=ap.parse_args()
    raw_bytes=Path(ns.raw).read_bytes()
    raw=json.loads(raw_bytes)
    audit=audit_obj(raw)
    audit["raw_sha256"]=hashlib.sha256(raw_bytes).hexdigest()
    if ns.controls:
        kinds=["omit_candidate","extra_nonmax","wrong_top1","truth_out_of_range","raw_byte","duplicate_id","missing_row","authority_true","score_tamper"]
        results={}
        for k in kinds:
            a=audit_obj(mutated(raw,k))
            results[k]={"rejected": bool(a["errors"]), "errors": a["errors"][:4]}
        audit["corruption_controls"]=results
        audit["corruption_rejected"]=sum(v["rejected"] for v in results.values())
        if audit["corruption_rejected"] != len(kinds):
            audit["errors"].append("corruption_control_failure")
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if not audit["errors"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
