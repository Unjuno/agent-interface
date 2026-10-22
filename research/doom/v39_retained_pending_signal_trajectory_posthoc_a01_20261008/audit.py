"""Independent audit of the retained V39 trajectory reconstruction."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


class AuditError(ValueError):
    pass


def _load_inputs():
    raw = {}
    for name, pin in FREEZE["inputs"].items():
        try:
            value = subprocess.check_output(
                ["git", "show", f"{FREEZE['source_commit']}:{pin['path']}"],
                cwd=ROOT,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as error:
            raise AuditError(f"cannot read frozen input {name}") from error
        if len(value) != pin["bytes"] or hashlib.sha256(value).hexdigest() != pin["sha256"]:
            raise AuditError(f"frozen input integrity failure: {name}")
        raw[name] = value
    if raw["events"] != raw["delivered"]:
        raise AuditError("delivered event stream differs byte-for-byte")
    return raw


def _rows(data):
    return [json.loads(line) for line in data.splitlines()]


def _file_name(path):
    return path.replace("\\", "/").rsplit("/", 1)[-1]


def audit_result(candidate):
    raw = _load_inputs()
    report = json.loads(raw["report"])
    events = _rows(raw["events"])
    typed = [row for row in events if row.get("event") == "typed_observation"]
    observations = [row for row in events if row.get("event") == "observation"]
    expected = FREEZE["expected"]
    if len(typed) != 218 or [row.get("sequence") for row in typed] != list(range(1, 219)):
        raise AuditError("typed observations are not the frozen contiguous 1..218 sequence")
    full_by_seq = {row.get("sequence"): row for row in observations}
    typed_by_seq = {row["sequence"]: row for row in typed}
    if len(full_by_seq) != 218 or len(typed_by_seq) != 218:
        raise AuditError("observation cardinality or sequence uniqueness failed")
    for row in typed:
        pair = full_by_seq.get(row["sequence"])
        if pair is None:
            raise AuditError(f"no full observation pairs with sequence {row['sequence']}")
        for field in ("id", "step", "capture_ns", "pointer_binding", "frame_rgb_sha256"):
            if pair.get(field) != row.get(field):
                raise AuditError(f"paired record mismatch at {row['sequence']}: {field}")
        for signal_name in ("health", "ammo"):
            signal = row.get("signals", {}).get(signal_name)
            if (not isinstance(signal, dict) or signal.get("sequence") != row["sequence"] or
                    signal.get("capture_ns") != row["capture_ns"] or
                    signal.get("binding") != row["pointer_binding"] or
                    type(signal.get("value")) is not int):
                raise AuditError(f"typed {signal_name} receipt mismatch at {row['sequence']}")

    image_rows = {_file_name(row["image"]): row for row in observations}
    if len(report.get("decisions", [])) != 6:
        raise AuditError("report does not contain six decisions")
    observed_windows = []
    for index, decision in enumerate(report["decisions"]):
        source_event = image_rows.get(_file_name(decision.get("source_image", "")))
        if source_event is None:
            raise AuditError(f"decision {index}: source image unresolved")
        start = source_event["sequence"]
        terminal_ns = decision.get("planner_terminal_observed_ns")
        if type(terminal_ns) is not int:
            raise AuditError(f"decision {index}: terminal timestamp absent")
        source = typed_by_seq.get(start)
        if source is None or source["frame_rgb_sha256"] != source_event["frame_rgb_sha256"]:
            raise AuditError(f"decision {index}: source observation mismatch")
        window = [r for r in typed if r["sequence"] >= start and r["capture_ns"] <= terminal_ns]
        if not window:
            raise AuditError(f"decision {index}: no observations before terminal")
        changes = []
        prior = object()
        for row in window:
            values = (row["signals"]["health"]["value"], row["signals"]["ammo"]["value"])
            if values != prior:
                changes.append([row["sequence"], values[0], values[1]])
                prior = values
        observed_windows.append({
            "decision": index,
            "source_sequence": start,
            "source_health": source["signals"]["health"]["value"],
            "source_ammo": source["signals"]["ammo"]["value"],
            "source_capture_ns": source["capture_ns"],
            "planner_terminal_observed_ns": terminal_ns,
            "model_ns": decision.get("model_ns"),
            "end_sequence": window[-1]["sequence"],
            "end_capture_ns": window[-1]["capture_ns"],
            "health_ammo_changes": changes,
        })
    if [row["end_sequence"] for row in observed_windows] != expected["window_end_sequences"]:
        raise AuditError("one or more pending window terminal sequences differ")
    if candidate.get("windows") != observed_windows:
        raise AuditError("candidate window table differs from independent reconstruction")

    observed_guards = []
    for index, decision in enumerate(report["decisions"]):
        source_iteration = decision.get("cover_policy_source_iteration")
        if source_iteration is None:
            continue
        admission = decision.get("cover_validity_admission")
        if not isinstance(admission, dict) or admission.get("status") != "admitted":
            raise AuditError(f"decision {index}: active cover lacks admitted guard")
        source = admission.get("source_signal", {})
        authored = admission.get("authored", {})
        effective = admission.get("effective", {})
        start = source.get("sequence")
        if start != observed_windows[index]["source_sequence"]:
            raise AuditError(f"decision {index}: guard source sequence differs")
        floor = max(authored.get("critical_health_minimum"),
                    source.get("value") - authored.get("maximum_health_loss"))
        if floor != effective.get("hard_minimum"):
            raise AuditError(f"decision {index}: source and effective guard floor differ")
        window_end = observed_windows[index]["end_sequence"]
        rows = [r for r in typed if start <= r["sequence"] <= window_end]
        equal = [r["sequence"] for r in rows if r["signals"]["health"]["value"] == floor]
        below = [r["sequence"] for r in rows if r["signals"]["health"]["value"] < floor]
        invalidation = decision.get("policy_invalidation")
        invalidation_seq = invalidation.get("sequence") if isinstance(invalidation, dict) else None
        soft = decision.get("cover_validity_latest_soft_event")
        soft_seq = soft.get("sequence") if isinstance(soft, dict) else None
        if (below[0] if below else None) != invalidation_seq:
            raise AuditError(f"decision {index}: first below-floor row differs from invalidation")
        observed_guards.append({
            "decision": index,
            "active_cover_source_iteration": source_iteration,
            "source_sequence": start,
            "source_health": source["value"],
            "hard_minimum": floor,
            "equal_sequences": equal,
            "below_sequences": below,
            "reported_soft_event_sequence": soft_seq,
            "reported_invalidation_sequence": invalidation_seq,
        })
    if observed_guards != expected["guarded_decisions"]:
        raise AuditError("guard boundary rows differ from independent frozen expectations")
    if candidate.get("active_cover_guard_windows") != [
        {**guard, "critical_health_minimum": report["decisions"][guard["decision"]]["cover_validity_admission"]["authored"]["critical_health_minimum"],
         "maximum_health_loss": report["decisions"][guard["decision"]]["cover_validity_admission"]["authored"]["maximum_health_loss"],
         "strict_rule": "hard invalidation iff observed health < hard_minimum"}
        for guard in observed_guards
    ]:
        raise AuditError("candidate guard table differs from independent raw reconstruction")

    score = json.loads(raw["score"])
    disposition = {
        "kills": score.get("kill_count"),
        "deaths": score.get("death_count"),
        "map_exit": score.get("map_exit"),
        "episode_finished": score.get("episode_finished"),
        "player_dead": score.get("player_dead"),
        "claim": report.get("claim"),
    }
    if candidate.get("episode_disposition") != disposition:
        raise AuditError("candidate episode disposition differs from retained scorer")
    for key, value in {
        "source_commit": FREEZE["source_commit"],
        "typed_observations": 218,
        "paired_full_observations": 218,
        "event_rows": len(events),
        "event_streams_byte_identical": True,
        "sequences_contiguous": True,
        "episode_disposition": disposition,
    }.items():
        if candidate.get(key) != value:
            raise AuditError(f"candidate top-level field differs: {key}")
    candidate_hash = hashlib.sha256(
        (json.dumps(candidate, indent=2, sort_keys=True) + "\n").encode("utf-8")
    ).hexdigest()
    return {
        "schema": "v39-retained-pending-trajectory-audit-v2",
        "status": "PASS_INDEPENDENT_RAW_RECONSTRUCTION",
        "checks": {
            "pinned_inputs": True,
            "event_streams_byte_identical": True,
            "typed_sequences_1_to_218": True,
            "paired_observations_218": True,
            "six_windows_and_transitions": True,
            "authored_guard_boundaries": True,
            "scorer_terminal_disposition": True,
            "candidate_result_sha256": candidate_hash,
        },
        "scope": "independent posthoc audit of pinned Git blobs; template-derived HUD values; no causal, live-current-main, or task-completion claim",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result", nargs="?", type=Path, default=HERE / "RESULT.json")
    args = parser.parse_args()
    candidate = json.loads(args.result.read_text(encoding="utf-8"))
    print(json.dumps(audit_result(candidate), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()