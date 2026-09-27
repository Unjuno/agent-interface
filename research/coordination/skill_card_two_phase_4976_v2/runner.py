from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import base_model
import candidate

CASE_PATH = ROOT / "cases.json"
SOURCE_FILES = {
    "base_model.py": ROOT / "base_model.py",
    "cases.json": CASE_PATH,
    "candidate.py": ROOT / "candidate.py",
    "runner.py": ROOT / "runner.py",
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def registry_hash() -> str:
    payload = {key: asdict(skill) for key, skill in base_model.REGISTRY.items()}
    return sha(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())

def ident(event_type: str, session: candidate.Session, **extra):
    return {"type": event_type, "session_id": session.session_id,
            "case_id": session.case_id, **extra}

def execute_rows():
    cases = json.loads(CASE_PATH.read_text(encoding="utf-8"))
    rows = []
    for index, case in enumerate(cases):
        session = candidate.present_candidates(case, base_model, f"session-{index:02d}")
        preselection_loads = list(session.loader.loaded)
        key = case["expected_key"]
        selected_status = candidate.select_candidate(
            session, ident("SELECT_CANDIDATE", session, candidate_key=key))
        receipt = None
        if selected_status == "REVALIDATION_REQUIRED":
            receipt = candidate.revalidate_current(
                session, ident("REVALIDATE_CURRENT", session), base_model)
        result = candidate.load_selected_detail(
            session, ident("LOAD_SELECTED_DETAIL", session), base_model, receipt)
        rows.append({
            "case_id": case["case_id"],
            "expected_key": key,
            "expected_status": case["expected_status"],
            "selected_key": session.selected_key,
            "selected_status": selected_status,
            "final_status": result["status"],
            "candidate_keys": list(session.candidates),
            "filter_log": session.trace[0]["filter_log"],
            "preselection_detail_loads": preselection_loads,
            "detail_loaded": result["detail_loaded"],
            "detail": result["detail"],
            "revalidation_receipt": receipt,
            "events": result["trace"],
        })
    return rows

def run_control(control_id, operation):
    case = next(c for c in json.loads(CASE_PATH.read_text(encoding="utf-8"))
                if c["case_id"] == "hint_with_revalidation")
    session = candidate.present_candidates(case, base_model, "control-" + control_id)
    reason = None
    try:
        operation(session)
    except candidate.BoundaryError as exc:
        reason = str(exc)
    return {"control_id": control_id, "refused": reason is not None,
            "reason": reason, "detail_loaded": list(session.loader.loaded),
            "events": list(session.trace)}

def negative_controls():
    out = []
    out.append(run_control(
        "no_selection",
        lambda s: candidate.load_selected_detail(
            s, ident("LOAD_SELECTED_DETAIL", s), base_model)))
    out.append(run_control(
        "wrong_candidate",
        lambda s: candidate.select_candidate(
            s, ident("SELECT_CANDIDATE", s, candidate_key="not-presented"))))
    out.append(run_control(
        "hint_before_revalidation",
        lambda s: (candidate.select_candidate(
            s, ident("SELECT_CANDIDATE", s, candidate_key="cached_route_v1")),
            candidate.load_selected_detail(
                s, ident("LOAD_SELECTED_DETAIL", s), base_model))))
    def wrong_session(s):
        candidate.select_candidate(s, ident("SELECT_CANDIDATE", s, candidate_key="cached_route_v1"))
        own = candidate.revalidate_current(s, ident("REVALIDATE_CURRENT", s), base_model)
        altered = dict(own, session_id="another-session")
        candidate.load_selected_detail(s, ident("LOAD_SELECTED_DETAIL", s), base_model, altered)
    out.append(run_control("wrong_session_receipt", wrong_session))
    def stale_receipt(s):
        candidate.select_candidate(s, ident("SELECT_CANDIDATE", s, candidate_key="cached_route_v1"))
        own = candidate.revalidate_current(s, ident("REVALIDATE_CURRENT", s), base_model)
        candidate.load_selected_detail(s, ident("LOAD_SELECTED_DETAIL", s), base_model,
                                       dict(own, freshness="STALE"))
    out.append(run_control("stale_receipt", stale_receipt))
    def tampered_provenance(s):
        candidate.select_candidate(s, ident("SELECT_CANDIDATE", s, candidate_key="cached_route_v1"))
        own = candidate.revalidate_current(s, ident("REVALIDATE_CURRENT", s), base_model)
        candidate.load_selected_detail(s, ident("LOAD_SELECTED_DETAIL", s), base_model,
                                       dict(own, source_provenance="forged"))
    out.append(run_control("tampered_provenance", tampered_provenance))
    out.append(run_control(
        "hint_role_promotion",
        lambda s: (_ for _ in ()).throw(candidate.BoundaryError("registry_promotion_rejected"))
        if not base_model.validate_registry_entry({
            **asdict(base_model.REGISTRY["cached_route_v1"]),
            "mutate_hint_in_place_to_admission": True,
        })[0] else None))
    return out

def main(out_path: str):
    before = registry_hash()
    rows = execute_rows()
    controls = negative_controls()
    after = registry_hash()
    payload = {
        "schema": "skill-card-two-phase-4976-raw-v1",
        "issue": 4998,
        "allocation": "skill-card-two-phase-4976-20260928-02",
        "main_commit": "4fa988e2872e20f4da840c91fbdd83a8d0ff8d12",
        "source_hashes": {name: sha(path.read_bytes()) for name, path in SOURCE_FILES.items()},
        "registry_sha256_before": before,
        "registry_sha256_after": after,
        "rows": rows,
        "negative_controls": controls,
        "model_calls": 0, "gui_calls": 0, "action_emissions": 0, "authority_grants": 0,
    }
    Path(out_path).write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"issue": 4998, "rows": len(rows), "controls": len(controls),
                      "output": out_path}, sort_keys=True))

if __name__ == "__main__":
    main(sys.argv[1])
