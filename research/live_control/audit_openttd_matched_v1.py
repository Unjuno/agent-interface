"""Audit and summarize the preregistered matched OpenTTD model-route study."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

from append_checkpoint_v1 import inspect, load
from openttd_proposal_schema_v5 import parse
from received_continuation_v1 import advance, start
from timing_envelope_v1 import interval, validate

HERE = Path(__file__).resolve().parent
BASE = HERE / "results/timing-envelope-openttd-matched-01"
sys.path.insert(0, str(HERE.parent / "observation_tiles"))
from tile_transport import Decoder


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def source_with_hash(path: Path, digest: str) -> Path:
    if path.exists() and sha(path) == digest:
        return path
    archived = HERE / "frozen_sources" / digest / path.name
    assert archived.exists() and sha(archived) == digest, str(path)
    return archived


def expected_route(arm: str, turn: int):
    if arm == "fixed-luna":
        return "gpt-5.6-luna", "low"
    if arm == "fixed-astra":
        return "gpt-6-astra", "medium"
    return ("gpt-5.6-luna", "low") if turn <= 2 else ("gpt-6-astra", "medium")


def per_turn(timing, event, turn):
    return next(row for row in timing if row["event"] == event and row["details"].get("turn") == turn)


def audit_arm(arm: str):
    root = BASE / arm
    control = BASE / f"{arm}-control"
    runtime = root / "runtime"
    for directory in (root, control):
        plan = read(directory / "plan.json")
        assert plan["arm"] == arm
        for name, digest in plan["sources"].items():
            source_with_hash(HERE / name, digest)
    manifest = read(runtime / "manifest.json")
    for name, digest in manifest["sources"].items():
        source_with_hash(HERE.parent / name, digest)

    endpoint = read(root / "endpoint.json")
    events = [json.loads(line) for line in (runtime / "events.jsonl").read_text().splitlines()]
    calls = read(root / "calls.json")
    state = start(endpoint["socket"])

    def replay(exchange):
        nonlocal state
        request, reply = exchange["request"], exchange["reply"]
        assert request["after"] == state["cursor"]
        assert reply["records"] == events[request["after"]:reply["cursor"]]
        state = advance(state, endpoint["socket"], request["after"], reply)
        expected = exchange["state"]["continuation"] if "state" in exchange else exchange["continuation"]
        assert state == expected

    replay(read(root / "initial.json"))
    for call in calls:
        replay(call["result"])
        assert call["result"]["state"]["pending"] is None
    assert load(root / "journal.jsonl") == calls[-1]["result"]["state"]
    replay(read(root / "finish.json"))

    handoffs = read(control / "turns.json")
    turns = len(handoffs)
    candidates = list(root.glob("*.png")) + list(runtime.glob("*.png"))
    models = []
    act_turns = 0
    for turn in range(1, turns + 1):
        directory = root / f"model-{turn}"
        plan = read(directory / "plan.json")
        route = expected_route(arm, turn)
        assert (plan["requested_model"], plan["requested_effort"]) == route
        assert plan["runner_sha256"] == sha(HERE / "model_pair_runner_v2.py")
        assert sum(sha(image) == plan["image_sha256"] for image in candidates) == 1
        assert (directory / "prompt.txt").read_text() == (root / f"prompt-{turn}.txt").read_text()
        process = read(directory / "process.json")
        assert process["exit_code"] == 0
        lines = (directory / "events.jsonl").read_bytes().splitlines(keepends=True)
        arrivals = [json.loads(line) for line in (directory / "arrivals.jsonl").read_text().splitlines()]
        assert len(lines) == len(arrivals)
        for line, arrival in zip(lines, arrivals):
            assert sha_bytes(line) == arrival["sha256"] and len(line) == arrival["bytes"]
        records = [json.loads(line) for line in lines]
        items = [event["item"] for event in records if event.get("type") == "item.completed"]
        assert len(items) == 1 and items[0]["type"] == "agent_message"
        typed = parse(items[0]["text"])
        assert typed == read(root / f"typed-{turn}.json")
        usage = next(event["usage"] for event in records if event.get("type") == "turn.completed")
        models.append({
            "turn": turn,
            "model": route[0],
            "effort": route[1],
            "kind": typed["kind"],
            "usage": usage,
            "runner_wall_ms": (process["exited_ns"] - process["started_ns"]) / 1e6,
        })
        if typed["kind"] == "act":
            proposal = read(root / f"proposal-{turn}.json")
            assert proposal == {"steps": typed["steps"], "rationale": typed["rationale"]}
            applied = read(root / f"applied-{turn}.json")
            group = calls[act_turns * 4:(act_turns + 1) * 4]
            assert [call["result"]["request"]["command"]["op"] for call in group] == ["clock", "submit", "clock", "submit"]
            assert group[1]["result"]["request"]["command"]["steps"] == [{"op": "observe"}]
            assert group[3]["result"]["request"]["command"]["steps"] == typed["steps"] + [{"op": "observe"}]
            assert group[3]["result"] == applied["result"]
            act_turns += 1
        else:
            assert turn == turns and typed["kind"] == "verify" and typed["road_visible"] is True
            assert typed == read(root / "visual-verdict.json")
    assert len(calls) == act_turns * 4

    observations = [event for event in events if event.get("event") == "observation"]
    artifacts = sorted(runtime.glob("*.ait"))
    assert len(artifacts) == len(observations)
    decoder = Decoder("live-control")
    for artifact, event in zip(artifacts, observations):
        decoded = decoder.accept(artifact.read_bytes())
        with Image.open(runtime / Path(event["image"]).name) as image:
            assert (image.width, image.height, image.mode, image.tobytes()) == (
                decoded.width, decoded.height, decoded.mode, decoded.pixels
            )
    terminals = [event for event in events if event.get("event") == "terminal"]
    assert terminals and all(
        event["release"]["verified"] is True
        and event["release"]["keys_down"] == []
        and event["release"]["buttons_down"] == []
        for event in terminals
    )
    evaluation = next(event for event in events if event.get("event") == "independent_evaluation")
    success = evaluation["success"] is True
    if success:
        assert all(evaluation["checks"].values()) and evaluation["changed_surrounding_tiles"] == []
        assert read(control / "result.json")["success"] is True
        assert not (control / "error.json").exists() and not (root / "abort.json").exists()
    else:
        failure = read(root / "failure-evaluation.json")
        assert failure["success"] is False and failure["evaluation"] == evaluation
        assert read(control / "error.json")["automatic_retry"] is False

    timing = [validate(json.loads(line)) for line in (control / "timing-envelope.jsonl").read_text().splitlines()]
    assert [event["sequence"] for event in timing] == list(range(1, len(timing) + 1))
    observed = [event for event in timing if event["state"] == "OBSERVED"]
    assert len({event["clock"]["domain_id"] for event in observed}) == 1
    missing = [event for event in timing if event["state"] == "NOT_RECORDED"]
    assert {event["event"] for event in missing} == {
        "runtime_receipt", "os_injection", "provider_request_received", "provider_first_token"
    }
    model_intervals = [
        interval(per_turn(timing, "planner_request_started", turn), per_turn(timing, "planner_proposal_received", turn))
        for turn in range(1, turns + 1)
    ]
    feedback_intervals = [
        interval(per_turn(timing, "proposal_published", turn), per_turn(timing, "first_useful_feedback_detected", turn))
        for turn in range(1, act_turns + 1)
    ]
    assert all(row["status"] == "comparable" for row in model_intervals + feedback_intervals)
    completion_ms = None
    uncertainty_ms = None
    if success:
        first = next(row for row in timing if row["event"] == "initial_observation_detected")
        final = next(row for row in timing if row["event"] == "semantic_completion_detected")
        whole = interval(first, final)
        assert whole == read(control / "result.json")["initial_observation_to_semantic_completion"]
        completion_ms = whole["duration_ns"] / 1e6
        uncertainty_ms = whole["uncertainty_ns"] / 1e6
    assert not Path(endpoint["socket"]).exists() and not Path(endpoint["cancel_socket"]).exists()
    return {
        "arm": arm,
        "audit_passed": True,
        "hard_success": success,
        "model_turns": models,
        "model_wait_total_ms": sum(row["duration_ns"] for row in model_intervals) / 1e6,
        "proposal_to_useful_feedback_ms": [row["duration_ns"] / 1e6 for row in feedback_intervals],
        "proposal_to_useful_feedback_total_ms": sum(row["duration_ns"] for row in feedback_intervals) / 1e6,
        "initial_observation_to_semantic_completion_ms": completion_ms,
        "initial_to_completion_uncertainty_ms": uncertainty_ms,
        "input_tokens_total": sum(row["usage"]["input_tokens"] for row in models),
        "cached_input_tokens_total": sum(row["usage"]["cached_input_tokens"] for row in models),
        "output_tokens_total": sum(row["usage"]["output_tokens"] for row in models),
        "reasoning_output_tokens_total": sum(row["usage"]["reasoning_output_tokens"] for row in models),
        "runtime_exact_frames": len(observations),
        "contact_sheets": len(list(root.glob("planner-*.png"))),
        "durable_calls": len(calls),
        "append_records": inspect(root / "journal.jsonl")[1],
        "save_sha256": manifest["save_sha256"],
        "task": read(root / "ready.json")["task"],
        "initial_geometry": read(root / "ready.json")["observation"]["pointer_binding"]["geometry"],
        "missing_endpoints": sorted(set(row["event"] for row in missing)),
        "independent_checks": evaluation["checks"],
        "changed_surrounding_tiles": evaluation["changed_surrounding_tiles"],
    }


def main():
    prereg = read(BASE / "preregistration.json")
    assert prereg["status"] == "PREREGISTERED_BEFORE_EXECUTION"
    assert prereg["execution_order"] == ["fixed-luna", "fixed-astra", "adaptive"]
    for name, digest in prereg["sources"].items():
        source_with_hash(HERE / name, digest)
    assert len({
        json.dumps(read(BASE / arm / "plan.json")["sources"], sort_keys=True)
        for arm in prereg["execution_order"]
    }) == 1
    assert len({
        json.dumps(read(BASE / f"{arm}-control" / "plan.json")["sources"], sort_keys=True)
        for arm in prereg["execution_order"]
    }) == 1
    arms = [audit_arm(arm) for arm in prereg["execution_order"]]
    assert len({arm["save_sha256"] for arm in arms}) == 1
    assert len({arm["task"] for arm in arms}) == 1
    assert len({tuple(arm["initial_geometry"]) for arm in arms}) == 1
    report = {
        "audit_passed": True,
        "preregistered": True,
        "matched_invariants": {
            "same_canonical_save_sha256": arms[0]["save_sha256"],
            "same_task": arms[0]["task"],
            "same_initial_geometry": arms[0]["initial_geometry"],
            "same_source_and_prompt_policy": True,
            "only_declared_model_route_varies": True,
        },
        "arms": arms,
        "scope": (
            "one fixed-order fresh episode per arm; descriptive matched evidence only; "
            "no latency distribution, randomized causal estimate, human comparison, or route promotion"
        ),
        "audit_sha256": sha(Path(__file__)),
    }
    (BASE / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
