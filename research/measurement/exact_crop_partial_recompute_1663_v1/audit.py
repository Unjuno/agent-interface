"""Independent raw-only audit for Issue #4083; imports neither study nor candidate."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import statistics
import struct

import numpy as np
from PIL import Image

SCORE_SCHEMA = "exact-rgb-crop-semantic-score-v1"
CONTRACT_SCHEMA = "exact-rgb-crop-semantic-probe-v1"


def frame_sha(width, height, mode, pixels):
    header = b"AIFR1\0" + mode.encode("ascii") + b"\0" + struct.pack("!II", width, height)
    return hashlib.sha256(header + pixels).hexdigest()


def expected(contract, image):
    assert contract["schema"] == CONTRACT_SCHEMA and contract["grants_input_authority"] is False
    with Image.open(image) as src:
        im = src.convert("RGB")
        pixels = im.tobytes()
        arr = np.frombuffer(pixels, np.uint8).reshape(im.height, im.width, 3)
    l, t, r, b = contract["box"]
    observed = hashlib.sha256(arr[t:b, l:r].tobytes()).hexdigest()
    success = observed == contract["expected_crop_sha256"]
    return {
        "schema": SCORE_SCHEMA,
        "probe_id": contract["probe_id"],
        "success": success,
        "reason": contract["success_reason"] if success else "expected_crop_missing",
        "box": list(contract["box"]),
        "observed_crop_sha256": observed,
        "expected_crop_sha256": contract["expected_crop_sha256"],
        "scored_frame_sha256": frame_sha(im.width, im.height, "RGB", pixels),
        "frame": {"width": im.width, "height": im.height, "mode": "RGB"},
        "grants_input_authority": False,
    }


def audit(rows):
    errors=[]; checks=0
    seen=set()
    for row in rows:
        key=(row.get("workload"), row.get("rep")); checks+=1
        if key in seen: errors.append("duplicate_case:"+repr(key))
        seen.add(key)
        if row.get("schema") != "exact-crop-partial-recompute-case-v1": errors.append("schema:"+repr(key))
        reqs=row.get("requests",[]); arms=row.get("arms",{})
        if len(reqs)!=24: errors.append("request_count:"+repr(key))
        for arm_name in ("BASELINE","CANDIDATE"):
            arm=arms.get(arm_name,{})
            if len(arm.get("outputs",[]))!=24: errors.append("output_count:"+arm_name+repr(key))
        for i, req in enumerate(reqs):
            exp=expected(req["contract"], req["image"])
            for arm_name in ("BASELINE","CANDIDATE"):
                checks+=1
                got=arms[arm_name]["outputs"][i]["result"]
                if got != exp: errors.append(f"result:{arm_name}:{key}:{i}")
                if got.get("grants_input_authority") is not False: errors.append(f"authority:{arm_name}:{key}:{i}")
        checks+=1
        if not row.get("all_equal") or not all(row.get("result_equal",[])): errors.append("cross_arm:"+repr(key))
    expected_keys={(w,r) for w in ("METADATA","ROI","IMAGE") for r in range(3)}
    if seen != expected_keys: errors.append("denominator")
    meta=[r for r in rows if r["workload"]=="METADATA"]
    ratios=[]
    for r in meta:
        b=r["arms"]["BASELINE"]["cpu_ns"]; c=r["arms"]["CANDIDATE"]["cpu_ns"]
        ratios.append(c/b)
    ratio_median=statistics.median(ratios) if ratios else None
    contract_pass=not errors
    cost_pass=contract_pass and ratio_median <= 0.75
    return {"schema":"exact-crop-partial-recompute-audit-v1","checks":checks,"errors":errors,
            "cases":len(rows),"requests":sum(len(r.get("requests",[])) for r in rows),
            "metadata_cpu_ratios":ratios,"metadata_cpu_ratio_median":ratio_median,
            "contract_decision":"PASS_EXACT_CROP_PARTIAL_RECOMPUTE_CONTRACT_SCOPED" if contract_pass else "FAIL_OR_HOLD",
            "cost_decision":"PASS_EXACT_CROP_PARTIAL_RECOMPUTE_COST_SCOPED" if cost_pass else "HOLD_PARTIAL_RECOMPUTE_COST_NOT_ESTABLISHED"}


def mutation_controls(rows):
    tests=[]
    muts=[]
    # Eight semantic/provenance mutations.
    x=copy.deepcopy(rows); x.pop(); muts.append(("missing_case",x))
    x=copy.deepcopy(rows); x.append(copy.deepcopy(x[0])); muts.append(("duplicate_case",x))
    x=copy.deepcopy(rows); x[0]["arms"]["CANDIDATE"]["outputs"][0]["result"]["probe_id"]="tampered"; muts.append(("result",x))
    x=copy.deepcopy(rows); x[0]["arms"]["CANDIDATE"]["outputs"][0]["result"]["grants_input_authority"]=True; muts.append(("authority",x))
    x=copy.deepcopy(rows); x[0]["requests"][0]["contract"]["expected_crop_sha256"]="0"*64; muts.append(("contract",x))
    x=copy.deepcopy(rows); x[0]["requests"].pop(); muts.append(("request_count",x))
    x=copy.deepcopy(rows); x[0]["all_equal"]=False; muts.append(("cross_arm",x))
    x=copy.deepcopy(rows); x[0]["schema"]="wrong"; muts.append(("schema",x))
    for name,data in muts:
        rejected=bool(audit(data)["errors"])
        tests.append({"name":name,"rejected":rejected})
    return tests


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("root",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args()
    rows=[]
    for p in sorted(a.root.glob("case-*.json")):
        rows.append(json.loads(p.read_text()))
    result=audit(rows); result["controls"]=mutation_controls(rows); result["controls_pass"]=all(x["rejected"] for x in result["controls"])
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if not result["errors"] and result["controls_pass"] else 1)

if __name__ == "__main__": main()
