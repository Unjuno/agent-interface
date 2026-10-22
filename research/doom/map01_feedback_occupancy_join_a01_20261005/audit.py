"""Independent recomputation of A01's retained-feedback/occupancy join."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FB = REPO / "research/doom/map01_first_useful_feedback_posthoc_v1"
OCC = REPO / "research/doom/results/map01-held-input-occupancy-fulltrace-v4/v39.json"
PUB = json.loads((FB / "publication_manifest.json").read_text())


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def independently_load_v39() -> tuple[dict, dict, str]:
    data = b"".join((FB / f"full_artifact.part{i:02d}.b64").read_bytes()
                    for i in range(4))
    archive_bytes = base64.b64decode(data, validate=True)
    assert digest(archive_bytes) == PUB["full_actions"]["artifact_zip_sha256"]
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
        result_raw = zf.read("result.json")
        audit_raw = zf.read("audit_result.json")
    assert digest(result_raw) == PUB["full_actions"]["result_json_sha256"]
    assert digest(audit_raw) == PUB["full_actions"]["audit_result_json_sha256"]
    report = json.loads(result_raw)
    run = next(x for x in report["runs"] if x["run"] == "map01-v39-coast-liveness-live-01")
    occupancy_bytes = OCC.read_bytes()
    occupancy = json.loads(occupancy_bytes)
    assert occupancy["source_sha256"]["runtime/events.jsonl"] == run["events_sha256"]
    assert occupancy["source_sha256"]["report.json"] == run["report_sha256"]
    return occupancy, run, digest(occupancy_bytes)


def relation(plan_ns: int, event: dict) -> str:
    if plan_ns < event["first_key_admitted_ns"]:
        return "BEFORE_INPUT_ADMISSION"
    if plan_ns < event["first_key_ack_ns"]:
        return "ADMISSION_IN_FLIGHT"
    if plan_ns <= event["confirmed_any_key_held_until_ns"]:
        return "WITHIN_GUARANTEED_ANY_KEY_OCCUPANCY"
    if plan_ns <= event["released_by_ns"]:
        return "RELEASE_TIME_UNRESOLVED"
    return "AFTER_RELEASE_UPPER_BOUND"


def main() -> None:
    occupancy, run, occ_sha = independently_load_v39()
    output = json.loads((HERE / "RESULT.json").read_text())
    expected_ids = {"plan-0-primary-0-1", "plan-3-primary-0-1", "plan-4-primary-0-1"}
    assert {p["id"] for p in output["plans"]} == expected_ids
    by_id = {p["id"]: p for p in output["plans"]}
    checked = 0
    for plan in run["plans"]:
        pid = plan["id"]
        got = by_id[pid]
        first = plan["earliest_state_feedback"]
        assert first is not None and got["feedback_capture_ns"] == first["capture_ns"]
        holds = [h for h in occupancy["holds"] if h["id"] == pid]
        assert len(holds) == len(got["hold_relations"])
        for h, joined in zip(holds, got["hold_relations"], strict=True):
            assert joined["step"] == h["step"]
            assert joined["admission_ns"] == h["first_key_admitted_ns"]
            assert joined["ack_ns"] == h["first_key_ack_ns"]
            assert joined["earliest_release_ns"] == h["confirmed_any_key_held_until_ns"]
            assert joined["latest_release_ns"] == h["released_by_ns"]
            assert joined["feedback_relation"] == relation(first["capture_ns"], h)
            checked += 1
    assert output["source_hashes"]["occupancy_sha256"] == occ_sha
    assert output["source_hashes"]["events_sha256"] == run["events_sha256"]
    assert output["source_hashes"]["report_sha256"] == run["report_sha256"]
    assert sum(r["feedback_relation"] == "WITHIN_GUARANTEED_ANY_KEY_OCCUPANCY"
               for p in output["plans"] for r in p["hold_relations"]) == 3
    assert any("no action-to-feedback causality" in item for item in output["limits"])
    print(json.dumps({"status": "PASS_INDEPENDENT_JOIN_AUDIT",
                      "plans": len(run["plans"]), "hold_relations": checked,
                      "guaranteed_occupancy_feedback_relations": 3,
                      "source_identity_match": True, "errors": 0}, indent=2))


if __name__ == "__main__":
    main()
