#!/usr/bin/env python3
"""Independent raw-only reconstruction and one-shot audit of the A04 table."""
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

EXPECTED_SHA256 = "ecffd8121a289d3533c94373c8f7aba50d9c349ffd5db534e46db16522897e9d"
CELLS = (("CASE_PATCH","CONTROLLED"),("CASE_PATCH","FULL"),("STRATUM_PATCH","CONTROLLED"),("STRATUM_PATCH","FULL"))
OUTCOMES = ("dev_accuracy","fresh_accuracy","optimism")


def frac(row, name):
    if name == "dev_accuracy": return Fraction(row["dev_correct"],row["dev_total"])
    if name == "fresh_accuracy": return Fraction(row["fresh_correct"],row["fresh_total"])
    return Fraction(str(row["optimism"]))


def summary(vector):
    if len(vector) != 100: raise ValueError("auditor vector length not 100")
    ordered = sorted(vector)
    return {"n":100,"mean_fraction":str(sum(vector,Fraction())/100),
            "median_fraction":str((ordered[49]+ordered[50])/2),"min_fraction":str(ordered[0]),
            "max_fraction":str(ordered[-1]),"positive":sum(v>0 for v in vector),
            "zero":sum(v==0 for v in vector),"negative":sum(v<0 for v in vector)}


def rebuild(raw, digest):
    if type(raw) is not list or len(raw) != 400: raise ValueError("row count is not 400")
    grouped = defaultdict(dict)
    for row in raw:
        if type(row) is not dict: raise ValueError("non-object raw row")
        cell=(row.get("updater"),row.get("feedback")); seed=row.get("seed")
        if cell not in CELLS or type(seed) is not int or not 0 <= seed < 100: raise ValueError("invalid raw key")
        if seed in grouped[cell]: raise ValueError("duplicate seed")
        integer_fields=("dev_correct","dev_total","fresh_correct","fresh_total","query_count","safety_veto_count")
        if any(type(row.get(k)) is not int for k in integer_fields): raise ValueError("noninteger raw protocol field")
        if row["dev_total"] != 32 or row["fresh_total"] != 32 or not 0 <= row["dev_correct"] <= 32 or not 0 <= row["fresh_correct"] <= 32: raise ValueError("invalid cohort outcome")
        if row["query_count"] != 5 or row["safety_veto_count"] != 1 or row.get("candidate_locked_before_fresh") is not True or row.get("raw_released_after_lock") is not True: raise ValueError("protocol accounting mismatch")
        if Fraction(str(row.get("optimism"))) != Fraction(row["dev_correct"]-row["fresh_correct"],32): raise ValueError("optimism raw field mismatch")
        grouped[cell][seed]=row
    if any(set(grouped[cell]) != set(range(100)) for cell in CELLS): raise ValueError("cell seed coverage mismatch")
    cells={}
    for u,f in CELLS:
        values=[grouped[(u,f)][i] for i in range(100)]
        cells.setdefault(u,{})[f]={"n":100,"safety_vetoes":sum(r["safety_veto_count"] for r in values),"metrics":{m:summary([frac(r,m) for r in values]) for m in OUTCOMES}}
    feedback={}
    for u in ("CASE_PATCH","STRATUM_PATCH"):
        feedback[u]={m:summary([frac(grouped[(u,"FULL")][i],m)-frac(grouped[(u,"CONTROLLED")][i],m) for i in range(100)]) for m in OUTCOMES}
    updater={}
    for f in ("CONTROLLED","FULL"):
        updater[f]={m:summary([frac(grouped[("CASE_PATCH",f)][i],m)-frac(grouped[("STRATUM_PATCH",f)][i],m) for i in range(100)]) for m in OUTCOMES}
    interaction={m:summary([(frac(grouped[("CASE_PATCH","FULL")][i],m)-frac(grouped[("CASE_PATCH","CONTROLLED")][i],m))-(frac(grouped[("STRATUM_PATCH","FULL")][i],m)-frac(grouped[("STRATUM_PATCH","CONTROLLED")][i],m)) for i in range(100)]) for m in OUTCOMES}
    return {"schema":"feedback-update-rule-factorial-analysis-v1","input_sha256":digest,"rows":400,"seeds_per_cell":100,
            "cell_summaries":cells,"feedback_full_minus_controlled_within_updater":feedback,
            "update_case_minus_stratum_within_feedback":updater,"interaction_case_minus_stratum_of_feedback_effect":interaction,
            "inference":"finite authored 100-seed fixture only; no p-value or population inference"}


def mutation_probes(expected):
    probes=[]
    for path, value in (("rows",399),("input_sha256","0"*64)):
        item=json.loads(json.dumps(expected)); item[path]=value; probes.append(item)
    for block, key in (("cell_summaries",None),("feedback_full_minus_controlled_within_updater",None),
                       ("update_case_minus_stratum_within_feedback",None),
                       ("interaction_case_minus_stratum_of_feedback_effect",None)):
        item=json.loads(json.dumps(expected))
        if block == "cell_summaries": del item[block]["CASE_PATCH"]["FULL"]
        elif block == "feedback_full_minus_controlled_within_updater": item[block]["CASE_PATCH"]["dev_accuracy"]["mean_fraction"]="9/1"
        elif block == "update_case_minus_stratum_within_feedback": item[block]["FULL"]["fresh_accuracy"]["n"]=99
        else: item[block]["optimism"]["negative"] += 1
        probes.append(item)
    return probes


def main(argv):
    if len(argv)!=4:
        print("usage: audit.py IMMUTABLE_RAW.json ANALYSIS.json AUDIT.json",file=sys.stderr);return 2
    try:
        raw_bytes=Path(argv[1]).read_bytes(); digest=hashlib.sha256(raw_bytes).hexdigest()
        if digest!=EXPECTED_SHA256: raise ValueError("immutable A01 raw SHA-256 mismatch")
        expected=rebuild(json.loads(raw_bytes.decode("utf-8")),digest)
        supplied=json.loads(Path(argv[2]).read_text(encoding="utf-8"))
        if supplied!=expected: raise ValueError("analysis differs from independent raw reconstruction")
        probes=mutation_probes(expected); rejected=sum(probe!=expected for probe in probes)
        record={"status":"PASS_ANALYSIS_AUDIT_SCOPED" if rejected==len(probes) else "FAIL_ANALYSIS_AUDIT",
                "input_sha256":digest,"rows_reconstructed":400,"analysis_output_matches":True,
                "mutation_controls":len(probes),"mutations_rejected":rejected,
                "scope":"independent reconstruction of retained finite raw; no candidate rerun or population inference"}
        out=Path(argv[3])
        if not out.parent.is_dir() or out.exists(): raise ValueError("audit output parent missing or output already exists")
        out.write_text(json.dumps(record,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
    except (OSError,UnicodeError,json.JSONDecodeError,ValueError) as exc:
        print(f"STOP_AUDIT_CONTRACT: {type(exc).__name__}: {exc}",file=sys.stderr);return 1
    print(json.dumps({"status":record["status"],"rows":400,"mutations_rejected":rejected},sort_keys=True));return 0 if record["status"]=="PASS_ANALYSIS_AUDIT_SCOPED" else 1

if __name__=="__main__": raise SystemExit(main(sys.argv))
