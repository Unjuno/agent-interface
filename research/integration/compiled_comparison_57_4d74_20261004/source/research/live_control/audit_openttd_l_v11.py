"""Audit the first changed-geometry OpenTTD L effect-memory allocation."""
import base64
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

from openttd_effect_memory_v1 import build as build_effect_memory
from semantic_checkpoint_v4 import next_checkpoint_turn, parse


HERE = Path(__file__).resolve().parent
BASE = HERE / "results/timing-envelope-openttd-l-11"
ROOT = BASE / "fixed-astra"
CONTROL = BASE / "fixed-astra-control"
sys.path.insert(0, str(HERE.parent / "openttd_task"))
from guarded_l_score_v1 import score  # noqa: E402


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def declared_source(name, expected):
    path = HERE.parent / name if name.startswith("openttd_task/") else HERE / name
    if path.exists() and sha(path) == expected:
        return path
    frozen = HERE / "frozen_sources" / expected / (Path(name).name + ".b64")
    if not frozen.exists():
        raise AssertionError(name)
    raw = base64.b64decode(frozen.read_text(encoding="ascii"))
    assert hashlib.sha256(raw).hexdigest() == expected
    return frozen


def observer_records(path):
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        marker = line.find("AIT ")
        if marker >= 0:
            result.append(json.loads(line[marker + 4:]))
    return result


def signature(record):
    return tuple((tile["id"], tile["road"], tile["owner"]) for tile in record["guard"])


def current_image(applied):
    observation = applied["result"]["state"]["continuation"]["observation"]
    return ROOT / "runtime" / Path(observation["image"]).name


def same_pixels(left, right):
    with Image.open(left) as first, Image.open(right) as second:
        return first.size == second.size and ImageChops.difference(
            first.convert("RGB"), second.convert("RGB")).getbbox() is None


def main():
    preregistration = read(BASE / "preregistration.json")
    assert preregistration["status"] == "preregistered_before_execution"
    assert preregistration["execution"] == "first and only model allocation; no retry or manual intervention"
    for name, expected in preregistration["sources"].items():
        declared_source(name, expected)
    for plan_path in (CONTROL / "plan.json", ROOT / "plan.json"):
        for name, expected in read(plan_path)["sources"].items():
            declared_source(name, expected)

    result = read(ROOT / "result.json")
    assert result["exit_code"] == 0
    assert result["finish_kind"] == "bounded_turn_limit"
    assert result["proposals_executed"] == 12 and result["journal_calls"] == 50
    assert result["success"] is True
    assert result["controller_outcome"] == "bounded_turn_limit_with_independent_task_success"
    evaluation = result["evaluation"]
    assert evaluation["success"] is True
    assert evaluation["checks"] == {
        "target_owned_roads": True,
        "ordered_bidirectional_connections": True,
        "forbidden_tiles_clear": True,
        "surrounding_road_owner_unchanged": True,
    }
    assert evaluation["contract"]["target"] == preregistration["task"]["target"]
    assert evaluation["contract"]["forbidden"] == preregistration["task"]["forbidden"]
    assert read(ROOT / "runtime/cleanup.json") == {
        "all_owned_processes_exited": True, "save_unchanged": True}

    error = read(CONTROL / "error.json")
    assert error == {
        "type": "RuntimeError",
        "detail": "driver exited before failure-evaluation.json",
        "automatic_retry": False,
    }
    assert not (CONTROL / "result.json").exists()

    turns = read(CONTROL / "turns.json")
    assert len(turns) == 12 and [row["kind"] for row in turns] == ["act"] * 12
    required = None
    typed = []
    usage = []
    for turn in range(1, 13):
        rows = [json.loads(line) for line in
                (ROOT / f"model-{turn}/events.jsonl").read_text(encoding="utf-8").splitlines()]
        message = next(row["item"]["text"] for row in rows if row.get("type") == "item.completed")
        proposal = parse(message, required, "transparent")
        assert proposal == read(ROOT / f"typed-{turn}.json")
        typed.append(proposal)
        usage.append(next(row["usage"] for row in rows if row.get("type") == "turn.completed"))
        new_required = next_checkpoint_turn(turn, proposal)
        if new_required is not None:
            required = new_required
        elif required is not None and proposal["checkpoint"]["status"] == "observed":
            required = None
    assert required == 11
    assert [typed[index - 1]["checkpoint"]["status"] for index in range(6, 11)] == ["uncertain"] * 5
    assert typed[10]["checkpoint"]["prior_turn"] == 5
    assert typed[10]["checkpoint"]["status"] == "observed"
    assert typed[11]["checkpoint"]["prior_turn"] == 11
    assert typed[11]["checkpoint"]["status"] == "uncertain"

    drags = [(turn, step) for turn, proposal in enumerate(typed, 1)
             for step in proposal.get("steps", []) if step.get("op") == "pointer_drag"]
    assert [turn for turn, _ in drags] == [5, 11]
    assert drags[0][1]["points"] == [
        {"x": 705, "y": 239}, {"x": 673, "y": 255}, {"x": 641, "y": 271}]
    assert drags[1][1]["points"] == [
        {"x": 641, "y": 278}, {"x": 673, "y": 294}, {"x": 705, "y": 310}]

    replay = []
    effect = None
    with tempfile.TemporaryDirectory(prefix="audit-openttd-memory-v11-") as temporary:
        temporary = Path(temporary)
        for turn in range(5, 13):
            applied = read(ROOT / f"applied-{turn}.json")
            destination = temporary / f"planner-{turn + 1}.png"
            planner, effect = build_effect_memory(
                current_image(applied), applied, typed[turn - 1], ROOT / "runtime",
                destination, effect=effect, turn=turn)
            expected = ROOT / f"planner-{turn + 1}.png"
            assert same_pixels(planner, expected)
            replay.append({
                "after_turn": turn,
                "source_turn": effect["source_turn"],
                "inspection_turns": effect["inspection_turns"],
                "checked_in_sha256": sha(expected),
            })
    assert [(row["source_turn"], row["inspection_turns"]) for row in replay] == [
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (11, 0), (11, 1)]

    calls = read(ROOT / "calls.json")
    assert len(calls) == 50
    runtime_events = [json.loads(line) for line in
                      (ROOT / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [row for row in runtime_events if row.get("event") == "observation"]
    terminals = [row for row in runtime_events if row.get("event") == "terminal"]
    assert len(observations) == 62 and len(terminals) == 25
    assert all(row["release"]["verified"] and not row["release"]["keys_down"]
               and not row["release"]["buttons_down"] for row in terminals)

    observer_path = ROOT / "runtime/game-stderr.txt"
    observer = observer_records(observer_path)
    assert len(observer) == 252
    transitions = [index for index in range(1, len(observer))
                   if signature(observer[index]) != signature(observer[index - 1])]
    assert transitions == [94, 236]
    changed_tiles = []
    for index in transitions:
        before = {tile["id"]: tile for tile in observer[index - 1]["guard"]}
        after = {tile["id"]: tile for tile in observer[index]["guard"]}
        changed_tiles.append([tile for tile in before if before[tile] != after[tile]])
    assert changed_tiles == [[684, 685, 686], [750, 814]]
    final_score = score(observer[-1], observer[0])
    assert final_score == {key: evaluation[key] for key in
                           ("success", "checks", "changed_surrounding_tiles", "contract")}
    assert all(signature(row) == signature(observer[-1]) for row in observer[236:])

    input_tokens = sum(row["input_tokens"] for row in usage)
    cached_tokens = sum(row["cached_input_tokens"] for row in usage)
    output_tokens = sum(row["output_tokens"] for row in usage)
    assert (input_tokens, cached_tokens, output_tokens) == (204114, 104448, 2751)
    model_wait_ms = sum(row["model_runner_returned_ns"] - row["model_runner_started_ns"]
                        for row in turns) / 1e6
    feedback_ms = sum(row["applied_read_ns"] - row["proposal_published_ns"]
                      for row in turns) / 1e6
    assert model_wait_ms == 195604.2648 and feedback_ms == 27466.6396
    timing = [json.loads(line) for line in
              (CONTROL / "timing-envelope.jsonl").read_text(encoding="utf-8").splitlines()]
    initial_ns = next(row["timestamp_ns"] for row in timing
                      if row.get("event") == "initial_observation_detected")
    post_second_drag_feedback_ms = (turns[10]["applied_read_ns"] - initial_ns) / 1e6
    assert post_second_drag_feedback_ms == 211631.6066
    assert not any(row.get("event") == "semantic_completion_detected" for row in timing)

    runtime_manifest = read(ROOT / "runtime/manifest.json")
    assert runtime_manifest["save_sha256"] == preregistration["task"]["save_sha256"]
    assert "seed-991003" in runtime_manifest["scope"]
    report = {
        "audit_passed": True,
        "preregistered": True,
        "independent_task_success": True,
        "controller_verified_hard_success": False,
        "finish_kind": result["finish_kind"],
        "controller_outcome": result["controller_outcome"],
        "independent_checks": evaluation["checks"],
        "model_turns": len(turns),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "model_wait_ms": model_wait_ms,
        "proposal_to_feedback_ms": feedback_ms,
        "initial_to_post_second_drag_feedback_ms": post_second_drag_feedback_ms,
        "semantic_completion_detected_ms": None,
        "durable_calls": len(calls),
        "runtime_exact_frames": len(observations),
        "verified_release_terminals": len(terminals),
        "drag_attempts": [{"turn": turn, **step} for turn, step in drags],
        "repeated_completed_segment_drags": 0,
        "effect_memory_replay": replay,
        "observer": {
            "records": len(observer),
            "transition_indices": transitions,
            "transition_tiles": changed_tiles,
            "stable_complete_records": len(observer) - transitions[-1],
            "score": final_score,
            "source_sha256": sha(observer_path),
        },
        "defects": {
            "semantic_completion_not_declared_before_limit": True,
            "supervisor_expected_failure_filename_after_successful_limit_score": True,
            "runtime_manifest_scope_retained_seed991003_text": True,
            "tracked_pointer_v9_was_overwritten_during_v11_and_restored_from_head": True,
        },
        "frozen_executed_pointer_source_sha256": preregistration["sources"]["pointer_socket_entry_v9.py"],
        "decision": "HOLD_EFFECT_MEMORY;_FIX_COMPLETION_FEEDBACK_AND_PACKAGING_BEFORE_ANOTHER_GEOMETRY_RUN",
        "scope": "one changed-geometry episode with independent task success at the turn limit; no verified completion, speed, token, population, human-tempo or cross-domain claim",
        "audit_sha256": sha(Path(__file__)),
    }
    (BASE / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
