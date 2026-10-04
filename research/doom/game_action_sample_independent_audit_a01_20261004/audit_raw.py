"""Independent raw-only reconstruction for retained ViZDoom action samples."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


SOURCE_COMMIT = "fe5a9dddf11f0351eb65001f1a1ddb867e8a5012"
SOURCE_PREFIX = "research/doom/game_action_sampling_59_4d74_20261004/construction03/"
INPUTS = {
    "scorer_last_action": "scorer-last-action.jsonl",
    "runtime_events": "runtime/events.jsonl",
    "runtime_scorer_samples": "runtime/scorer-samples.jsonl",
    "runtime_environment": "runtime/environment.json",
    "outer_probe_final": "PROBE_FINAL.json",
}
EXPECTED_SHA256 = {
    "scorer_last_action": "7270cb19ff9f29533331b5cac05b3ffb29a5e069cb1c9cb5a00ea31f6b663f85",
    "runtime_events": "d0c81931ea5674a7c815fa3fbd423ecf0c4283464c50817355e8abb33e44dec5",
    "runtime_scorer_samples": "22df0c14478a17f4007cded43e44b47e3094ae2ff782159a02f5e5e92998b2c7",
    "runtime_environment": "625d324a359c53b86eeffff6927398c47318d2fa2b821b7b9ea2396243b451ac",
    "outer_probe_final": "4d00d8f6c964a47727645cd1c3f9bb416fca81c062650a355f5bee59ab6d0da3",
}
BUTTONS = [
    "Button.TURN_LEFT",
    "Button.TURN_RIGHT",
    "Button.MOVE_FORWARD",
    "Button.MOVE_BACKWARD",
    "Button.MOVE_LEFT",
    "Button.MOVE_RIGHT",
    "Button.ATTACK",
    "Button.USE",
    "Button.SPEED",
]


class AuditError(AssertionError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def source_bytes(name: str) -> bytes:
    path = SOURCE_PREFIX + INPUTS[name]
    return subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{path}"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def load_inputs() -> tuple[dict[str, bytes], dict[str, object]]:
    freeze = json.loads(Path(__file__).with_name("FREEZE.json").read_text(encoding="utf-8"))
    require(freeze.get("source_commit") == SOURCE_COMMIT, "FREEZE source commit mismatch")
    require(freeze.get("source_sha256") == EXPECTED_SHA256, "FREEZE source hashes mismatch")
    blobs = {name: source_bytes(name) for name in INPUTS}
    digests = {name: hashlib.sha256(blob).hexdigest() for name, blob in blobs.items()}
    for name, expected in EXPECTED_SHA256.items():
        require(digests[name] == expected, f"source hash mismatch: {name}")

    def jsonl(name: str) -> list[dict[str, object]]:
        return [json.loads(line) for line in blobs[name].splitlines() if line.strip()]

    records: dict[str, object] = {
        "scorer_last_action": jsonl("scorer_last_action"),
        "runtime_events": jsonl("runtime_events"),
        "runtime_scorer_samples": jsonl("runtime_scorer_samples"),
        "runtime_environment": json.loads(blobs["runtime_environment"]),
        "outer_probe_final": json.loads(blobs["outer_probe_final"]),
        "source_sha256": digests,
    }
    return blobs, records


def audit(records: dict[str, object]) -> dict[str, object]:
    action_rows = records["scorer_last_action"]
    events = records["runtime_events"]
    score_rows = records["runtime_scorer_samples"]
    environment = records["runtime_environment"]
    final = records["outer_probe_final"]

    require(isinstance(action_rows, list) and len(action_rows) == 717, "unexpected action sample count")
    for index, row in enumerate(action_rows):
        require(row.get("event") == "scorer_last_action", f"wrong row kind at sample {index}")
        require(row.get("buttons") == BUTTONS, f"button ordering drift at sample {index}")
        action = row.get("action")
        require(isinstance(action, list) and len(action) == len(BUTTONS), f"wrong action width at sample {index}")
        require(all(value in (0, 1, 0.0, 1.0) for value in action), f"nonbinary action at sample {index}")
        require(row.get("coherent_tic") is True, f"incoherent sample tic at sample {index}")
        require(row.get("tic_before") == row.get("tic_after"), f"tic changed within sample {index}")
        require(row.get("authority") is False, f"controller-visible authority at sample {index}")
        require(row["sample_started_ns"] <= row["sample_returned_ns"], f"reversed sample bracket at sample {index}")

    active_indexes = [i for i, row in enumerate(action_rows) if row["action"][0] == 1]
    require(len(active_indexes) == 8, "unexpected number of TURN_LEFT samples")
    require(active_indexes == list(range(active_indexes[0], active_indexes[0] + 8)), "active samples not one row run")
    for i in active_indexes:
        require(action_rows[i]["action"] == [1.0] + [0.0] * 8, f"non-Left button active at sample {i}")

    first_i, last_i = active_indexes[0], active_indexes[-1]
    require(first_i > 0 and last_i + 1 < len(action_rows), "missing outside sample bracket")
    before_i = first_i - 1
    after_i = last_i + 1
    require(not any(action_rows[before_i]["action"]), "pre-Left sample is not neutral")
    require(not any(action_rows[after_i]["action"]), "post-Left sample is not neutral")

    accepted = [e for e in events if e.get("event") == "accepted" and e.get("id") == "left-action-probe"]
    admissions = [e for e in events if e.get("event") == "input_admission" and e.get("id") == "left-action-probe"]
    held = [e for e in events if e.get("event") == "keys_held" and e.get("id") == "left-action-probe"]
    releases = [e for e in events if e.get("event") == "input_release_transition" and e.get("id") == "left-action-probe"]
    require(len(accepted) == len(admissions) == len(held) == len(releases) == 1, "submit/admission/held/release event count mismatch")
    submit, admission, held_event, release = accepted[0], admissions[0], held[0], releases[0]
    receipt = release["owner_thread_keyup_receipt"]
    require(submit["steps"] == 2 and submit["intent_token"] == admission["intent_token"], "accepted submit identity/shape mismatch")
    require(admission["key"] == "Left" and held_event["keys"] == ["Left"] and release["key"] == "Left", "input key identity mismatch")
    require(admission["intent_token"] == release["intent_token"] == receipt["intent_token"], "intent identity mismatch")
    require(admission["owner_id"] == release["owner_id"] == receipt["owner_id"], "owner identity mismatch")
    require(receipt["key"] == "Left" and receipt["operation"] == "up", "wrong nested key-up receipt")
    require(receipt["server_sync_completed"] is True, "server XSync did not complete")
    require(receipt["physical_verification_authoritative"] is False, "physical release overclaim")
    require(release["physical_verification_authoritative"] is False, "release event overclaims physical verification")
    require(admission["admitted_ns"] <= admission["input_ack_ns"] < held_event["input_ack_ns"], "input admission and held acknowledgement order mismatch")
    require(
        release["release_call_started_ns"]
        <= receipt["owner_keyrelease_started_ns"]
        <= receipt["owner_sync_returned_ns"]
        <= release["release_call_returned_ns"],
        "nested XTest/XSync key-up receipt falls outside its explicit-up bracket",
    )
    require(action_rows[before_i]["sample_returned_ns"] < admission["admitted_ns"], "pre-sample is not before admission")
    require(action_rows[first_i]["sample_started_ns"] > held_event["input_ack_ns"], "first active sample predates held acknowledgement")
    require(all(action_rows[i]["sample_started_ns"] > held_event["input_ack_ns"] for i in active_indexes), "active sample predates held acknowledgement")
    require(action_rows[last_i]["sample_returned_ns"] < release["release_call_started_ns"], "last active sample overlaps release call")
    require(all(action_rows[i]["sample_returned_ns"] < release["release_call_started_ns"] for i in active_indexes), "active sample overlaps release call")
    require(action_rows[after_i]["sample_started_ns"] > release["emit_ns"], "first neutral sample predates release publication")

    require(environment.get("mode") == "Mode.ASYNC_SPECTATOR", "unexpected ViZDoom mode")
    require(len(score_rows) == 715, "unexpected independent scorer sample count")
    require(all(row.get("controller_visible") is False for row in score_rows), "scorer update visible to controller")
    payloads = [row["payload"] for row in score_rows]
    require(max(p["kill_count"] for p in payloads) == 0, "positive kill count in retained scorer rows")
    require(max(p["death_count"] for p in payloads) == 0, "positive death count in retained scorer rows")
    require(all(not p["map_exit"] and not p["player_dead"] and not p["episode_finished"] for p in payloads), "terminal/progress claim contradicts scorer rows")
    measured_fields = {key.lower() for payload in payloads for key in payload}
    require(not any("health" in key or "ammo" in key or "damage" in key for key in measured_fields), "damage/ammo telemetry unexpectedly present")

    terminal = [e for e in events if e.get("event") == "terminal" and e.get("id") == "left-action-probe"]
    rejected = [e for e in events if e.get("event") == "rejected"]
    require(len(terminal) == 1 and terminal[0].get("status") == "completed", "inner program terminal missing")
    require(terminal[0]["release"].get("verified") is True and terminal[0]["release"].get("keys_down") == [], "terminal release is not empty/verified")
    require(any(e.get("reason") == "unsupported command" for e in rejected), "unsupported top-level command STOP absent")
    require(final.get("child_exit") == -9 and final.get("external_rescue_used") is True and final.get("reader_alive") is True, "outer cleanup STOP no longer matches raw record")

    tics = [action_rows[i]["tic_before"] for i in active_indexes]
    require(tics == [1375, 1376, 1377, 1379, 1380, 1381, 1382, 1383], "active sample tic set changed")
    return {
        "disposition": "PASS_SAMPLED_GAME_ACTION_STATE_SCOPED_AND_STOP_PROTOCOL_COMPLETION",
        "source_commit": SOURCE_COMMIT,
        "source_sha256": records["source_sha256"],
        "action_sample_count": len(action_rows),
        "coherent_action_sample_count": len(action_rows),
        "active_turn_left_sample_count": len(active_indexes),
        "active_sample_indexes_zero_based": active_indexes,
        "active_sample_tics": tics,
        "unobserved_tic_inside_active_span": 1378,
        "input_admission_ns": admission["admitted_ns"],
        "input_ack_ns": admission["input_ack_ns"],
        "keys_held_ack_ns": held_event["input_ack_ns"],
        "pre_active_neutral_sample": {"index": before_i, "tic": action_rows[before_i]["tic_before"], "returned_ns": action_rows[before_i]["sample_returned_ns"]},
        "first_active_sample": {"index": first_i, "tic": action_rows[first_i]["tic_before"], "started_ns": action_rows[first_i]["sample_started_ns"], "returned_ns": action_rows[first_i]["sample_returned_ns"]},
        "last_active_sample": {"index": last_i, "tic": action_rows[last_i]["tic_before"], "started_ns": action_rows[last_i]["sample_started_ns"], "returned_ns": action_rows[last_i]["sample_returned_ns"]},
        "owner_keyup_bracket_ns": [receipt["owner_keyrelease_started_ns"], receipt["owner_sync_returned_ns"]],
        "input_release_event_emit_ns": release["emit_ns"],
        "first_post_release_neutral_sample": {"index": after_i, "tic": action_rows[after_i]["tic_before"], "started_ns": action_rows[after_i]["sample_started_ns"], "returned_ns": action_rows[after_i]["sample_returned_ns"]},
        "scorer_sample_count": len(score_rows),
        "max_kills": max(p["kill_count"] for p in payloads),
        "max_deaths": max(p["death_count"] for p in payloads),
        "map_exit_observed": any(p["map_exit"] for p in payloads),
        "damage_or_ammo_measured": False,
        "inner_program_terminal": "completed",
        "outer_child_exit": final["child_exit"],
        "external_rescue_used": final["external_rescue_used"],
        "outer_reader_alive": final["reader_alive"],
        "interpretation": "eight sampled active values and a later neutral value are joined to the same Left intent and XSync up bracket; tic 1378 was not sampled; no useful recovery or normal protocol finish is shown",
    }


def load_and_audit() -> dict[str, object]:
    _, records = load_inputs()
    return audit(records)


def main() -> None:
    result = load_and_audit()
    (Path(__file__).with_name("AUDIT.json")).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
