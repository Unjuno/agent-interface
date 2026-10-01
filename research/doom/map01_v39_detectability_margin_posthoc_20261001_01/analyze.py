from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = REPO / "research/doom/results/map01-v39-coast-liveness-live-01"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def source_errors(freeze: dict) -> list[str]:
    errors = []
    for rel, expected in freeze["source_sha256"].items():
        path = REPO / rel
        if not path.is_file() or sha(path) != expected:
            errors.append("source_sha256:" + rel)
    for seq, expected in freeze["png_sha256"].items():
        path = RUN / "runtime" / f"{int(seq):03}.png"
        if not path.is_file() or sha(path) != expected:
            errors.append("png_sha256:" + str(seq))
    return errors


def derive(report: dict, events: list[dict], protocol: list[dict], visual: dict) -> dict:
    wanted = {61, 62, 70, 71, 76, 81, 90}
    typed = {
        row.get("sequence"): row
        for row in events
        if row.get("event") == "typed_observation" and row.get("sequence") in wanted
    }
    observations = {
        row.get("sequence"): row
        for row in events
        if row.get("event") == "observation" and row.get("sequence") in wanted
    }
    if not wanted.issubset(typed) or not wanted.issubset(observations):
        raise ValueError("selected exact observations incomplete")

    turns = [
        row for row in protocol
        if row.get("direction") == "sent"
        and (row.get("message") or {}).get("method") == "turn/start"
        and row.get("observed_ns") == 55518341448372
    ]
    if len(turns) != 1:
        raise ValueError("selected model request not unique")
    start = turns[0]["observed_ns"]
    text = turns[0]["message"]["params"]["input"][0]["text"]
    if "Current locally verified health: 85." not in text:
        raise ValueError("model-request source health mismatch")
    if "Current locally verified ammo: 44." not in text:
        raise ValueError("model-request source ammo mismatch")
    if '"sequence":62' not in text:
        raise ValueError("prompt does not bind prior typed event sequence")

    def signal(seq, name):
        return typed[seq]["signals"][name]["value"]

    timeline = []
    for seq in sorted(wanted):
        obs, row = observations[seq], typed[seq]
        if obs.get("capture_ns") != row.get("capture_ns"):
            raise ValueError("capture timestamp mismatch:" + str(seq))
        if obs.get("frame_rgb_sha256") != row.get("frame_rgb_sha256"):
            raise ValueError("frame RGB identity mismatch:" + str(seq))
        timeline.append({
            "sequence": seq,
            "capture_ns": row["capture_ns"],
            "emit_ns": row["emit_ns"],
            "health": signal(seq, "health"),
            "ammo": signal(seq, "ammo"),
            "frame_rgb_sha256": row["frame_rgb_sha256"],
        })

    pre_request = [
        row for row in events
        if row.get("event") == "typed_observation"
        and row.get("emit_ns", start + 1) <= start
    ]
    latest_pre_request = max(pre_request, key=lambda row: (row["emit_ns"], row["sequence"]))
    if latest_pre_request["sequence"] != 71:
        raise ValueError("latest typed observation before request changed")
    if latest_pre_request["signals"]["health"]["value"] != 85 or latest_pre_request["signals"]["ammo"]["value"] != 44:
        raise ValueError("latest pre-request typed state mismatch")

    during_wait = sorted(
        (row for row in events
         if row.get("event") == "typed_observation"
         and start < row.get("capture_ns", 0) <= report["decisions"][2]["planner_terminal_observed_ns"]),
        key=lambda row: (row["capture_ns"], row["sequence"]),
    )
    first_loss_row = next(
        row for row in during_wait if row["signals"]["health"]["value"] < 85
    )
    first_loss = next(row for row in timeline if row["sequence"] == first_loss_row["sequence"])
    if first_loss["sequence"] != 76 or first_loss["health"] != 82:
        raise ValueError("first post-request health decrement differs from frozen discriminator")

    decision = report["decisions"][2]
    if decision["final_action_admission"]["status"] != "REJECTED_ACTION_NOT_CURRENT":
        raise ValueError("selected turn terminal changed")
    if decision["final_action_admission"]["action_validity"]["snapshot"]["sequence"] != 91:
        raise ValueError("selected turn terminal observation changed")

    visual_witnesses = {row["sequence"] for row in visual["witnesses"]}
    if not {61, 70, 71, 76, 81, 90}.issubset(visual_witnesses):
        raise ValueError("visual annotation inventory incomplete")

    return {
        "schema": "map01-v39-detectability-margin-posthoc-v1",
        "cell": "v39 decision index 2; request at health 85, ammo 44",
        "status": "HOLD_NO_EFFECTIVE_INTERVENTION_BOUND_V39_CELL",
        "model_request_start_ns": start,
        "visible_by_sequence": 61,
        "visible_by_capture_ns": observations[61]["capture_ns"],
        "latest_typed_state_available_before_request": {
            "sequence": latest_pre_request["sequence"],
            "capture_ns": latest_pre_request["capture_ns"],
            "emit_ns": latest_pre_request["emit_ns"],
            "health": latest_pre_request["signals"]["health"]["value"],
            "ammo": latest_pre_request["signals"]["ammo"]["value"],
        },
        "first_observed_health_loss": first_loss,
        "request_to_first_loss_capture_ms": (first_loss["capture_ns"] - start) / 1_000_000,
        "request_to_first_loss_delivery_ms": (first_loss["emit_ns"] - start) / 1_000_000,
        "timeline": timeline,
        "decision_status_after_model": decision["final_action_admission"]["status"],
        "decision_reason_after_model": decision["final_action_admission"]["reason"],
        "t_gate_ns": None,
        "t_effective_ns": None,
        "t_harm_irreversible_ns": None,
        "classification": "UNKNOWN_INTERVENTION_MARGIN",
        "interpretation": "Threat was visible before a subsequent typed HUD health decrement during model wait, but this cell records no local guard decision or effective intervention; HUD health loss is not an irreversible-harm oracle.",
        "scope": "read-only posthoc reconstruction of one retained v39 synthetic fixture episode; no candidate, model, game, container, or input invocation",
    }


def main() -> int:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    errors = source_errors(freeze)
    if errors:
        result = {"schema": "map01-v39-detectability-margin-posthoc-v1", "status": "STOP_POSTHOC_AUDIT", "errors": errors}
    else:
        report = json.loads((RUN / "report.json").read_text(encoding="utf-8"))
        events = load_jsonl(RUN / "runtime/events.jsonl")
        protocol = load_jsonl(RUN / "planner-protocol.jsonl")
        visual = json.loads((HERE / "VISUAL_READ.json").read_text(encoding="utf-8"))
        try:
            result = derive(report, events, protocol, visual)
            result["errors"] = []
        except (KeyError, StopIteration, TypeError, ValueError) as exc:
            result = {"schema": "map01-v39-detectability-margin-posthoc-v1", "status": "STOP_POSTHOC_AUDIT", "errors": [type(exc).__name__ + ":" + str(exc)]}
    out = HERE / "RESULT.json"
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": result.get("errors", [])}, sort_keys=True))
    return 0 if result["status"] != "STOP_POSTHOC_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
