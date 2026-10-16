"""Resolve A01 boundary ties to exact retained in-hold observation events."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DOOM = REPO / "research/doom"
FB = DOOM / "map01_first_useful_feedback_posthoc_v1"
OCC = DOOM / "results/map01-held-input-occupancy-fulltrace-v7/v39.json"
EVENTS = DOOM / "results/v39-control-telemetry-gap-audit-20261004/events.jsonl"
PUBLICATION = json.loads((FB / "publication_manifest.json").read_text())


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load() -> tuple[dict, dict, list[dict], dict]:
    occupancy_raw = OCC.read_bytes()
    event_raw = EVENTS.read_bytes()
    occupancy = json.loads(occupancy_raw)
    events = [json.loads(line) for line in event_raw.splitlines()]
    assert sha(event_raw) == occupancy["source_sha256"]["runtime/events.jsonl"]
    assert sha(event_raw) == "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"

    chunks = b"".join((FB / f"full_artifact.part{i:02d}.b64").read_bytes() for i in range(4))
    artifact = base64.b64decode(chunks, validate=True)
    spec = PUBLICATION["full_actions"]
    assert sha(artifact) == spec["artifact_zip_sha256"]
    with zipfile.ZipFile(io.BytesIO(artifact)) as zf:
        result_raw = zf.read("result.json")
        audit_raw = zf.read("audit_result.json")
    assert sha(result_raw) == spec["result_json_sha256"]
    assert sha(audit_raw) == spec["audit_result_json_sha256"]
    feedback = json.loads(result_raw)
    run = next(x for x in feedback["runs"] if x["run"] == occupancy["run"])
    assert run["events_sha256"] == sha(event_raw)
    assert run["report_sha256"] == occupancy["source_sha256"]["report.json"]
    hashes = {"occupancy_v7_sha256": sha(occupancy_raw), "event_stream_sha256": sha(event_raw),
              "feedback_artifact_zip_sha256": sha(artifact), "feedback_result_sha256": sha(result_raw),
              "feedback_audit_member_sha256": sha(audit_raw)}
    return occupancy, run, events, hashes


def build() -> dict:
    occupancy, run, events, hashes = load()
    reports = []
    for plan in run["plans"]:
        feedback = plan["earliest_state_feedback"]
        assert feedback is not None
        stamp, sequence, pid = feedback["capture_ns"], feedback["sequence"], plan["id"]
        typed = [e for e in events if e.get("event") == "typed_observation" and
                 e.get("id") == pid and e.get("sequence") == sequence and e.get("capture_ns") == stamp]
        visual = [e for e in events if e.get("event") == "observation" and
                  e.get("id") == pid and e.get("sequence") == sequence and e.get("capture_ns") == stamp]
        assert len(typed) == len(visual) == 1
        assert typed[0]["frame_rgb_sha256"] == visual[0]["frame_rgb_sha256"]
        assert typed[0]["signals"]["health"]["value"] == feedback["to"]["health"]
        assert typed[0]["signals"]["ammo"]["value"] == feedback["to"]["ammo"]

        matching_holds = [h for h in occupancy["holds"] if h["id"] == pid and
                          h["step"] == visual[0]["step"]]
        assert len(matching_holds) == 1
        hold = matching_holds[0]
        assert hold["first_key_ack_ns"] <= stamp <= hold["confirmed_any_key_held_until_ns"]
        reports.append({"id": pid, "step": visual[0]["step"], "sequence": sequence,
                        "capture_ns": stamp, "frame_rgb_sha256": visual[0]["frame_rgb_sha256"],
                        "independent_state_change": feedback["changed"],
                        "from": feedback["from"], "to": feedback["to"],
                        "hold_keys": hold["requested_keys"],
                        "first_key_ack_ns": hold["first_key_ack_ns"],
                        "confirmed_any_key_held_until_ns": hold["confirmed_any_key_held_until_ns"],
                        "is_final_confirming_sample": stamp == hold["confirmed_any_key_held_until_ns"],
                        "observation_relation": "IN_HOLD_LOOP_AND_WITHIN_CONFIRMED_ANY_KEY_INTERVAL"})

    assert len(reports) == 3
    assert sum(r["is_final_confirming_sample"] for r in reports) == 2
    return {"schema": "map01-feedback-occupancy-exact-event-join-a02",
            "status": "PASS_EXACT_IN_HOLD_FEEDBACK_EVENT_IDENTITY_SCOPED",
            "run": occupancy["run"], "source_hashes": hashes, "plans": reports,
            "interpretation": "Each independently reconstructed first HUD feedback capture is the exact same timestamped frame event recorded inside its primary hold step. Two are the final sample used for the any-key-held confirmation bound; one is earlier in that interval.",
            "limits": ["software-side in-hold observation and any-key confirmation only; no per-key physical release identity",
                       "no action-to-feedback causality; multiple keys and changing game state remain possible causes",
                       "health/ammo changes are decision-relevant, not necessarily beneficial",
                       "three plans from one retained stochastic episode; no live run or allocation"]}


if __name__ == "__main__":
    result = build()
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "plans": [
        {"id": p["id"], "sequence": p["sequence"],
         "is_final_confirming_sample": p["is_final_confirming_sample"]}
        for p in result["plans"]]}, indent=2))
