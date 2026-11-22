"""Independent audit of exact v39 in-hold feedback event identity."""
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


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> None:
    occ_bytes, event_bytes = OCC.read_bytes(), EVENTS.read_bytes()
    occ = json.loads(occ_bytes)
    events = [json.loads(row) for row in event_bytes.splitlines()]
    assert digest(event_bytes) == "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"
    assert digest(event_bytes) == occ["source_sha256"]["runtime/events.jsonl"]

    publication = json.loads((FB / "publication_manifest.json").read_text())
    chunks = b"".join((FB / f"full_artifact.part{i:02d}.b64").read_bytes() for i in range(4))
    archive = base64.b64decode(chunks, validate=True)
    spec = publication["full_actions"]
    assert digest(archive) == spec["artifact_zip_sha256"]
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        result_bytes, audit_bytes = zf.read("result.json"), zf.read("audit_result.json")
    assert digest(result_bytes) == spec["result_json_sha256"]
    assert digest(audit_bytes) == spec["audit_result_json_sha256"]
    result = json.loads(result_bytes)
    run = next(r for r in result["runs"] if r["run"] == occ["run"])
    assert run["events_sha256"] == digest(event_bytes)
    out = json.loads((HERE / "RESULT.json").read_text())

    checks, endpoint_ties = 0, 0
    for plan in run["plans"]:
        pid = plan["id"]
        feedback = plan["earliest_state_feedback"]
        assert feedback is not None
        seq, stamp = feedback["sequence"], feedback["capture_ns"]
        typed = [e for e in events if e.get("event") == "typed_observation" and e.get("id") == pid and
                 e.get("sequence") == seq and e.get("capture_ns") == stamp]
        visual = [e for e in events if e.get("event") == "observation" and e.get("id") == pid and
                  e.get("sequence") == seq and e.get("capture_ns") == stamp]
        assert len(typed) == len(visual) == 1
        assert typed[0]["frame_rgb_sha256"] == visual[0]["frame_rgb_sha256"]
        hold = next(h for h in occ["holds"] if h["id"] == pid and h["step"] == visual[0]["step"])
        assert hold["first_key_ack_ns"] <= stamp <= hold["confirmed_any_key_held_until_ns"]
        row = next(p for p in out["plans"] if p["id"] == pid)
        assert row["sequence"] == seq and row["capture_ns"] == stamp
        assert row["frame_rgb_sha256"] == visual[0]["frame_rgb_sha256"]
        assert row["confirmed_any_key_held_until_ns"] == hold["confirmed_any_key_held_until_ns"]
        assert row["is_final_confirming_sample"] == (stamp == hold["confirmed_any_key_held_until_ns"])
        endpoint_ties += int(stamp == hold["confirmed_any_key_held_until_ns"])
        checks += 1
    assert checks == 3 and endpoint_ties == 2
    assert out["status"] == "PASS_EXACT_IN_HOLD_FEEDBACK_EVENT_IDENTITY_SCOPED"
    assert any("no action-to-feedback causality" in lim for lim in out["limits"])
    print(json.dumps({"status": "PASS_A02_INDEPENDENT_RAW_EVENT_AUDIT", "feedback_events": checks,
                      "exact_observation_identity_matches": checks, "confirming_endpoint_ties": endpoint_ties,
                      "source_hashes_match": True, "errors": 0}, indent=2))


if __name__ == "__main__":
    main()
