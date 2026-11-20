"""Join retained v39 first-HUD-feedback timestamps to hold release bounds."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FEEDBACK = REPO / "research/doom/map01_first_useful_feedback_posthoc_v1"
OCCUPANCY = REPO / "research/doom/results/map01-held-input-occupancy-fulltrace-v4/v39.json"
PUBLICATION = json.loads((FEEDBACK / "publication_manifest.json").read_text())
CHUNK_NAMES = [f"full_artifact.part{i:02d}.b64" for i in range(4)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_inputs() -> tuple[dict, dict, dict]:
    occ_bytes = OCCUPANCY.read_bytes()
    occupancy = json.loads(occ_bytes)
    assert occupancy["run"] == "map01-v39-coast-liveness-live-01"
    # publication_manifest records Git blob ids; the decoded full result binds the
    # runtime event SHA directly, which must match the occupancy reconstruction.
    encoded = "".join((FEEDBACK / name).read_text() for name in CHUNK_NAMES)
    artifact = base64.b64decode("".join(encoded.split()), validate=True)
    full = PUBLICATION["full_actions"]
    assert sha(artifact) == full["artifact_zip_sha256"]
    with zipfile.ZipFile(io.BytesIO(artifact)) as archive:
        assert sha(archive.read("result.json")) == full["result_json_sha256"]
        assert sha(archive.read("audit_result.json")) == full["audit_result_json_sha256"]
        result = json.loads(archive.read("result.json"))
    v39 = next(run for run in result["runs"] if run["run"] == occupancy["run"])
    assert v39["events_sha256"] == occupancy["source_sha256"]["runtime/events.jsonl"]
    assert v39["report_sha256"] == occupancy["source_sha256"]["report.json"]
    return occupancy, v39, {"occupancy_sha256": sha(occ_bytes),
                             "artifact_zip_sha256": sha(artifact),
                             "result_json_sha256": full["result_json_sha256"],
                             "events_sha256": v39["events_sha256"],
                             "report_sha256": v39["report_sha256"]}


def classify(plan: dict, holds: list[dict]) -> dict:
    feedback = plan["earliest_state_feedback"]
    if feedback is None:
        return {"id": plan["id"], "classification": "NO_RETAINED_STATE_FEEDBACK"}
    stamp = feedback["capture_ns"]
    rows = []
    for hold in holds:
        admitted = hold["first_key_admitted_ns"]
        acknowledged = hold["first_key_ack_ns"]
        earliest_release = hold["confirmed_any_key_held_until_ns"]
        latest_release = hold["released_by_ns"]
        if stamp < admitted:
            relation = "BEFORE_INPUT_ADMISSION"
        elif stamp < acknowledged:
            relation = "ADMISSION_IN_FLIGHT"
        elif stamp <= earliest_release:
            relation = "WITHIN_GUARANTEED_ANY_KEY_OCCUPANCY"
        elif stamp <= latest_release:
            relation = "RELEASE_TIME_UNRESOLVED"
        else:
            relation = "AFTER_RELEASE_UPPER_BOUND"
        rows.append({"step": hold["step"], "keys": hold["requested_keys"],
                     "admission_ns": admitted, "ack_ns": acknowledged,
                     "earliest_release_ns": earliest_release,
                     "latest_release_ns": latest_release,
                     "feedback_relation": relation})
    return {"id": plan["id"], "accepted_ns": plan["accepted_ns"],
            "feedback_capture_ns": stamp,
            "feedback_after_acceptance_ms": feedback["accepted_to_feedback_ms"],
            "feedback": feedback["changed"], "from": feedback["from"], "to": feedback["to"],
            "hold_relations": rows}


def build() -> dict:
    occupancy, v39, sources = read_inputs()
    joined = []
    for plan in v39["plans"]:
        holds = [h for h in occupancy["holds"] if h["id"] == plan["id"]]
        joined.append(classify(plan, holds))
    return {"schema": "map01-feedback-occupancy-join-a01",
            "status": "PASS_SAME_RUN_CLOCK_JOIN_SCOPED",
            "run": occupancy["run"], "source_hashes": sources,
            "plans": joined,
            "interpretation": "First independently reconstructed health/ammo observations were joined to conservative per-hold release-time intervals using the same monotonic event clock and run identity.",
            "limits": ["association only; no action-to-feedback causality",
                       "health/ammo changes may be harmful or environmental",
                       "occupancy endpoints are intervals, not exact physical key-up times",
                       "three admitted plans from one retained stochastic run only",
                       "no live allocation, game, model, GUI, or input was run"]}


if __name__ == "__main__":
    out = build()
    (HERE / "RESULT.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"status": out["status"], "plans": [
        {"id": p["id"], "feedback_relation": [h["feedback_relation"] for h in p.get("hold_relations", [])]}
        for p in out["plans"]]}, indent=2))
