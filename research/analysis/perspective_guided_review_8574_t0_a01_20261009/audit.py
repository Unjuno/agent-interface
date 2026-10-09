"""Raw-only audit for Issue 8574 perspective-guided review T0 A01."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
PRIVATE = ROOT
ALLOWED_CASE = {"NO_DEFECT", "SOURCE_SUPPORTED_OMISSION", "UNSUPPORTED_ADDITION", "AMBIGUOUS_SOURCE", "WORDING_ONLY"}
ALLOWED_ADJ = {"SOURCE_SUPPORTED_OMISSION", "UNSUPPORTED_ADDITION", "AMBIGUOUS_SOURCE", "WORDING_ONLY", "NO_ACTIONABLE_FINDING"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root: Path = ROOT, results: Path = RESULTS, private: Path = PRIVATE) -> dict:
    errors=[]
    freeze=json.loads((root/"FREEZE.json").read_text())
    packet_a=json.loads((root/"blind_packet_order_a.json").read_text())
    packet_b=json.loads((root/"blind_packet_order_b.json").read_text())
    gold=json.loads((private/"gold.json").read_text())
    assignments=json.loads((results/"assignment_manifest.json").read_text())
    adjudication=json.loads((results/"adjudicated_blind.json").read_text())
    packets={"A":packet_a,"B":packet_b}
    gold_by={x["case_id"]:x for x in gold}
    arm_by={x["reviewer_id"]:x["arm"] for x in assignments["reviewers"]}
    reviewer_by={x["reviewer_id"]:x for x in assignments["reviewers"]}
    expected_ids=set(gold_by)
    if len(gold)!=16 or len(packet_a)!=16 or len(packet_b)!=16 or set(x["case_id"] for x in packet_a)!=expected_ids or set(x["case_id"] for x in packet_b)!=expected_ids:
        errors.append("case inventory mismatch")
    if len(assignments["reviewers"])!=6 or any(sum(1 for r in assignments["reviewers"] if r["arm"]==arm)!=2 for arm in ("checklist","freeform","perspective")):
        errors.append("reviewer allocation must be two per arm")
    if [x["case_id"] for x in packet_b] != [x["case_id"] for x in reversed(packet_a)]:
        errors.append("counterbalanced packet order mismatch")
    for item in assignments["reviewers"]:
        if item["packet_order"] not in packets:
            errors.append(f"{item['reviewer_id']}: invalid packet assignment")
            continue
        raw_path=results/f"raw_review_{item['reviewer_id']}.json"
        if not raw_path.is_file():
            errors.append(f"{item['reviewer_id']}: missing raw review")
            continue
        try:
            review=json.loads(raw_path.read_text())
        except Exception as exc:
            errors.append(f"{item['reviewer_id']}: raw JSON invalid: {type(exc).__name__}")
            continue
        expected_order=[x["case_id"] for x in packets[item["packet_order"]]]
        cases=review.get("cases",[])
        ids=[x.get("case_id") for x in cases]
        if review.get("reviewer_id") != item["reviewer_id"] or ids != expected_order:
            errors.append(f"{item['reviewer_id']}: reviewer identity or case assignment/order mismatch")
        for case in cases:
            if case.get("case_disposition") not in ALLOWED_CASE or type(case.get("findings")) is not list:
                errors.append(f"{item['reviewer_id']} {case.get('case_id')}: invalid review record")
            for finding in case.get("findings",[]):
                if not all(k in finding for k in ("classification","finding","source_support","verification_gap_or_extra","confidence")):
                    errors.append(f"{item['reviewer_id']} {case.get('case_id')}: incomplete finding")
                if finding.get("classification") not in ALLOWED_CASE or type(finding.get("confidence")) not in (int,float):
                    errors.append(f"{item['reviewer_id']} {case.get('case_id')}: invalid finding fields")
    adjudicated=adjudication.get("items",[])
    adj_map={}
    for entry in adjudicated:
        key=(entry.get("reviewer_id"),entry.get("case_id"),entry.get("finding_index"))
        if key in adj_map:
            errors.append(f"duplicate adjudication item {key}")
        adj_map[key]=entry
        if entry.get("decision") not in ALLOWED_ADJ or type(entry.get("cross_invariant_match")) is not bool:
            errors.append(f"invalid adjudication item {key}")
        if "arm" in entry or "gold_class" in entry or "source_case_id" in entry:
            errors.append(f"blind adjudicator output leaked hidden label {key}")
    qualifying={arm:[] for arm in ("checklist","freeform","perspective")}
    unsupported_controls=[]
    ambiguity_failures=[]
    for reviewer_id,arm in arm_by.items():
        raw_path=results/f"raw_review_{reviewer_id}.json"
        if not raw_path.is_file():
            continue
        review=json.loads(raw_path.read_text())
        for case in review["cases"]:
            gold_case=gold_by.get(case["case_id"],{})
            if gold_case.get("gold_class")=="ambiguous" and case.get("case_disposition")!="AMBIGUOUS_SOURCE":
                ambiguity_failures.append({"reviewer_id":reviewer_id,"case_id":case["case_id"],"disposition":case.get("case_disposition")})
            for index,finding in enumerate(case.get("findings",[])):
                adj=adj_map.get((reviewer_id,case["case_id"],index))
                if adj is None:
                    errors.append(f"missing adjudication {(reviewer_id,case['case_id'],index)}")
                    continue
                if gold_case.get("gold_class") in {"control","control_paraphrase"} and adj["decision"]=="UNSUPPORTED_ADDITION":
                    unsupported_controls.append({"reviewer_id":reviewer_id,"case_id":case["case_id"],"finding_index":index})
                if (gold_case.get("cross_clause_relations") and
                    adj["decision"]=="SOURCE_SUPPORTED_OMISSION" and adj["cross_invariant_match"]):
                    qualifying[arm].append({"reviewer_id":reviewer_id,"case_id":case["case_id"],"finding_index":index})
    pbr_incremental=bool(qualifying["perspective"] and not qualifying["checklist"] and not qualifying["freeform"])
    if ambiguity_failures:
        errors.append("one or more ambiguous source cases were forced into a definite disposition")
    if unsupported_controls:
        errors.append("one or more clean controls received unsupported additions")
    disposition=("PASS_METHOD_SCOPED" if not errors and pbr_incremental else
                 "NO_INCREMENTAL_VALUE_SCOPED" if not errors else "FAIL_AUDIT_OR_METHOD")
    return {"status":disposition,"case_count":len(gold),"reviewer_count":len(assignments["reviewers"]),
            "arm_counts":{a:sum(1 for x in assignments["reviewers"] if x["arm"]==a) for a in ("checklist","freeform","perspective")},
            "qualifying_cross_invariant_findings":qualifying,"pbr_incremental_rescue":pbr_incremental,
            "unsupported_control_findings":unsupported_controls,"ambiguity_failures":ambiguity_failures,
            "adjudication_item_count":len(adjudicated),"errors":errors,
            "scope":"Synthetic contract review by isolated Codex agent contexts; no human or GUI inference."}


if __name__ == "__main__":
    result=audit()
    (ROOT/"results"/"AUDIT.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["status"] in {"PASS_METHOD_SCOPED","NO_INCREMENTAL_VALUE_SCOPED"} else 1)
