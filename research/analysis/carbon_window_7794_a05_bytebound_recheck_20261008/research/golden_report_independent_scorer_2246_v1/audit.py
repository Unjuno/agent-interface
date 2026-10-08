from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
REPORT = REPO / "runtime/results/golden-desktop-app-server-v3-live-01/golden-report.json"
def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\\0".encode() + data).hexdigest()
def score(report: dict, provider_authority: bool = True, delivery: str = "certain") -> dict:
    if not provider_authority: return {"decision":"HOLD_NO_MODEL_AUTHORITY","model_calls":0,"input_events":0}
    if delivery != "certain": return {"decision":"HOLD_AMBIGUOUS_DELIVERY","model_calls":0,"input_events":0}
    tasks = report["tasks"]
    assert report["passed"] is True
    assert report["tasks_exact"] == 6 and len(tasks) == 6
    ev = report["independent_evaluation"]
    assert ev["success"] is True and ev["record_count"] == 6
    assert ev["unexpected"] == [] and ev["duplicates"] == {} and ev["missing"] == []
    assert all(t["submission_count"] == 1 and t["exact_submission"] for t in tasks)
    assert all(t["releases_verified"] and t["old_target_pointer_admissions"] == 0 for t in tasks)
    assert tasks[3]["repair"]["required"] and tasks[3]["repair"]["succeeded"]
    assert sum(len(t["model_calls"]) for t in tasks) == 2
    usage = report["usage"]
    assert usage["input_tokens"] == sum(c["usage"]["input_tokens"] for t in tasks for c in t["model_calls"])
    assert usage["output_tokens"] == sum(c["usage"]["output_tokens"] for t in tasks for c in t["model_calls"])
    canonical = json.dumps({"tasks":tasks,"evaluation":ev,"usage":usage}, sort_keys=True, separators=(",",":")).encode()
    return {"decision":"PASS_GOLDEN_REPORT_INDEPENDENT_SCORER_SCOPED","tasks":6,"exact_submissions":6,"model_calls":2,"releases_verified":6,"old_target_pointer_admissions":0,"canonical_sha256":hashlib.sha256(canonical).hexdigest()}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--report", default=str(REPORT)); a=p.parse_args()
    data=Path(a.report).read_bytes(); manifest=json.loads((ROOT/"SOURCE_MANIFEST.json").read_text())
    assert git_blob_sha(data) == manifest["report_blob_sha"]
    report=json.loads(data); positive=score(report)
    no_authority=score(report, provider_authority=False); ambiguous=score(report, delivery="ambiguous")
    assert no_authority["decision"] == "HOLD_NO_MODEL_AUTHORITY" and ambiguous["decision"] == "HOLD_AMBIGUOUS_DELIVERY"
    print(json.dumps({"positive":positive,"negative_controls":[no_authority,ambiguous],"report_blob_sha":git_blob_sha(data)}, sort_keys=True))
if __name__ == "__main__": main()
