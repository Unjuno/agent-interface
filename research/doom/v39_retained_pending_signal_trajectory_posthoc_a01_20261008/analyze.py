"""Reconstruct retained V39 HUD trajectories from pinned Git objects only."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


class EvidenceError(ValueError):
    pass


def verify_bytes(name, data):
    pin = FREEZE["inputs"][name]
    if len(data) != pin["bytes"]:
        raise EvidenceError(f"{name}: byte length differs from frozen source")
    digest = hashlib.sha256(data).hexdigest()
    if digest != pin["sha256"]:
        raise EvidenceError(f"{name}: SHA-256 differs from frozen source")
    return data


def load_inputs(git_show=subprocess.check_output):
    result = {}
    for name, pin in FREEZE["inputs"].items():
        try:
            data = git_show(
                ["git", "show", f"{FREEZE['source_commit']}:{pin['path']}"],
                cwd=ROOT,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as error:
            raise EvidenceError(f"cannot read pinned Git input {name}") from error
        result[name] = verify_bytes(name, data)
    return result


def _jsonl(data, label):
    try:
        return [json.loads(line) for line in data.splitlines()]
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceError(f"{label}: invalid JSONL") from error


def _basename(path):
    return path.replace("\\", "/").rsplit("/", 1)[-1]


def derive(inputs):
    for name, data in inputs.items():
        verify_bytes(name, data)
    if inputs["events"] != inputs["delivered"]:
        raise EvidenceError("source and delivered event streams differ")

    report = json.loads(inputs["report"])
    score = json.loads(inputs["score"] )
    events = _jsonl(inputs["events"], "events")
    typed = [row for row in events if row.get("event") == "typed_observation"]
    full = [row for row in events if row.get("event") == "observation"]
    expected = FREEZE["expected"]
    if len(typed) != expected["typed_observation_count"]:
        raise EvidenceError("typed observation count differs from freeze")
    if [row.get("sequence") for row in typed] != list(range(1, 219)):
        raise EvidenceError("typed observation sequence is not contiguous 1..218")
    full_by_sequence = {row.get("sequence"): row for row in full}
    if len(full_by_sequence) != expected["paired_observation_count"]:
        raise EvidenceError("full observation sequence cardinality differs")
    typed_by_sequence = {row["sequence"]: row for row in typed}
    if len(typed_by_sequence) != len(typed):
        raise EvidenceError("duplicate typed observation sequence")

    for row in typed:
        paired = full_by_sequence.get(row["sequence"])
        if paired is None:
            raise EvidenceError(f"missing paired full observation {row['sequence']}")
        for key in ("id", "step", "sequence", "capture_ns", "pointer_binding", "frame_rgb_sha256"):
            if paired.get(key) != row.get(key):
                raise EvidenceError(f"paired observation mismatch at sequence {row['sequence']}: {key}")
        for signal_name in ("health", "ammo"):
            signal = row.get("signals", {}).get(signal_name)
            if not isinstance(signal, dict):
                raise EvidenceError(f"missing {signal_name} at sequence {row['sequence']}")
            if (signal.get("sequence") != row["sequence"] or
                    signal.get("capture_ns") != row["capture_ns"] or
                    signal.get("binding") != row["pointer_binding"] or
                    type(signal.get("value")) is not int):
                raise EvidenceError(f"invalid paired {signal_name} at sequence {row['sequence']}")

    observation_by_image = {
        _basename(row["image"]): row for row in full if isinstance(row.get("image"), str)
    }
    decisions = report.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 6:
        raise EvidenceError("expected six report decisions")
    windows = []
    for index, decision in enumerate(decisions):
        source_name = _basename(decision.get("source_image", ""))
        source_full = observation_by_image.get(source_name)
        if source_full is None:
            raise EvidenceError(f"decision {index}: source image has no full observation")
        source_sequence = source_full["sequence"]
        source = typed_by_sequence.get(source_sequence)
        terminal_ns = decision.get("planner_terminal_observed_ns")
        if source is None or type(terminal_ns) is not int:
            raise EvidenceError(f"decision {index}: source or terminal clock absent")
        if source["frame_rgb_sha256"] != source_full["frame_rgb_sha256"]:
            raise EvidenceError(f"decision {index}: source frame hash mismatch")
        included = [
            row for row in typed
            if row["sequence"] >= source_sequence and row["capture_ns"] <= terminal_ns
        ]
        if not included:
            raise EvidenceError(f"decision {index}: empty pending window")
        previous = None
        changes = []
        for row in included:
            health = row["signals"]["health"]["value"]
            ammo = row["signals"]["ammo"]["value"]
            pair = (health, ammo)
            if pair != previous:
                changes.append([row["sequence"], health, ammo])
                previous = pair
        source_signals = source["signals"]
        windows.append({
            "decision": index,
            "source_sequence": source_sequence,
            "source_health": source_signals["health"]["value"],
            "source_ammo": source_signals["ammo"]["value"],
            "source_capture_ns": source["capture_ns"],
            "planner_terminal_observed_ns": terminal_ns,
            "model_ns": decision.get("model_ns"),
            "end_sequence": included[-1]["sequence"],
            "end_capture_ns": included[-1]["capture_ns"],
            "health_ammo_changes": changes,
        })
    if [row["end_sequence"] for row in windows] != expected["window_end_sequences"]:
        raise EvidenceError("pending-window terminal sequences differ from freeze")

    guarded = []
    expected_by_decision = {row["decision"]: row for row in expected["guarded_decisions"]}
    for index, decision in enumerate(decisions):
        source_iteration = decision.get("cover_policy_source_iteration")
        if source_iteration is None:
            continue
        admission = decision.get("cover_validity_admission")
        if not isinstance(admission, dict) or admission.get("status") != "admitted":
            raise EvidenceError(f"decision {index}: active cover has no admitted validity")
        source_signal = admission.get("source_signal")
        effective = admission.get("effective")
        authored = admission.get("authored")
        if not all(isinstance(x, dict) for x in (source_signal, effective, authored)):
            raise EvidenceError(f"decision {index}: malformed guard admission")
        source_sequence = source_signal.get("sequence")
        if source_sequence != windows[index]["source_sequence"]:
            raise EvidenceError(f"decision {index}: guard source does not match pending window")
        floor = max(
            authored.get("critical_health_minimum"),
            source_signal.get("value") - authored.get("maximum_health_loss"),
        )
        if floor != effective.get("hard_minimum"):
            raise EvidenceError(f"decision {index}: authored and effective health floors differ")
        rows = [row for row in typed if source_sequence <= row["sequence"] <= windows[index]["end_sequence"]]
        equal_sequences = [row["sequence"] for row in rows if row["signals"]["health"]["value"] == floor]
        below_sequences = [row["sequence"] for row in rows if row["signals"]["health"]["value"] < floor]
        soft = decision.get("cover_validity_latest_soft_event")
        invalidation = decision.get("policy_invalidation")
        observed_soft = soft.get("sequence") if isinstance(soft, dict) else None
        observed_invalidation = invalidation.get("sequence") if isinstance(invalidation, dict) else None
        first_below = below_sequences[0] if below_sequences else None
        if first_below != observed_invalidation:
            raise EvidenceError(f"decision {index}: first below-floor sample disagrees with invalidation")
        row = {
            "decision": index,
            "active_cover_source_iteration": source_iteration,
            "source_sequence": source_sequence,
            "source_health": source_signal["value"],
            "critical_health_minimum": authored["critical_health_minimum"],
            "maximum_health_loss": authored["maximum_health_loss"],
            "hard_minimum": floor,
            "equal_sequences": equal_sequences,
            "below_sequences": below_sequences,
            "reported_soft_event_sequence": observed_soft,
            "reported_invalidation_sequence": observed_invalidation,
            "strict_rule": "hard invalidation iff observed health < hard_minimum",
        }
        if expected_by_decision.get(index) != {
            key: row[key] for key in expected_by_decision.get(index, {})
        }:
            raise EvidenceError(f"decision {index}: guard boundary differs from freeze: expected={expected_by_decision.get(index)!r}, actual={row!r}")
        guarded.append(row)

    if [row["decision"] for row in guarded] != sorted(expected_by_decision):
        raise EvidenceError("guarded decision set differs from freeze")
    return {
        "schema": "v39-retained-pending-trajectory-result-v2",
        "source_commit": FREEZE["source_commit"],
        "inputs": {
            name: {
                "path": FREEZE["inputs"][name]["path"],
                "git_blob": FREEZE["inputs"][name]["git_blob"],
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            for name, data in inputs.items()
        },
        "event_streams_byte_identical": True,
        "event_rows": len(events),
        "typed_observations": len(typed),
        "paired_full_observations": len(full_by_sequence),
        "sequences_contiguous": True,
        "windows": windows,
        "active_cover_guard_windows": guarded,
        "episode_disposition": {
            "kills": score.get("kill_count"),
            "deaths": score.get("death_count"),
            "map_exit": score.get("map_exit"),
            "episode_finished": score.get("episode_finished"),
            "player_dead": score.get("player_dead"),
            "claim": report.get("claim"),
        },
        "scope": (
            "posthoc reconstruction of retained template-derived HUD and event data; "
            "no game/model/controller/GUI/OS input was run; no causal or independent game-state claim"
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="new result path; refuses to overwrite")
    args = parser.parse_args()
    result = derive(load_inputs())
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        if args.output.exists():
            raise SystemExit(f"refusing to overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")


if __name__ == "__main__":
    main()