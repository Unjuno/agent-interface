"""Audit retained setup failures and the successful receipt follow-up."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_control"
sys.path.insert(0, str(LIVE))

from audit_local_visual_barrier_v1 import Decoder, Frame
from mindustry_single_tile_score_v1 import score
from receipt_target_admission_v1 import evaluate


OUT = HERE / "results/mindustry-receipt-revalidation-followup-03"
ATTEMPT1 = HERE / "results/mindustry-receipt-revalidation-followup-01"
ATTEMPT2 = HERE / "results/mindustry-receipt-revalidation-followup-02"
FEASIBILITY1 = HERE / "results/mindustry-receipt-fault-controls-01"
FEASIBILITY2 = HERE / "results/mindustry-receipt-fault-controls-02"
FEASIBILITY3 = HERE / "results/mindustry-receipt-fault-controls-03"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def model_turn(root, row):
    stage = row["stage"]
    result = read(root / f"{stage}-result.json")
    process = read(root / stage / "process.json")
    events = [json.loads(line) for line in
              (root / stage / "events.jsonl").read_text().splitlines()]
    turns = [event for event in events if event.get("type") == "turn.completed"]
    messages = [event for event in events
                if event.get("type") == "item.completed" and
                event.get("item", {}).get("type") == "agent_message"]
    assert len(turns) == len(messages) == 1
    assert process["exit_code"] == 0
    assert process["requested_model"] == "gpt-5.6-luna"
    assert process["requested_effort"] == "low"
    assert turns[0]["usage"] == row["usage"] == result["usage"]
    assert json.loads(messages[0]["item"]["text"]) == result["typed"]


def audit_case(condition, reason):
    root = OUT / condition
    report = read(root / "report.json")
    result = report["result"]
    events = [json.loads(line) for line in
              (root / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    history = {}
    images = {}
    for index, observation in enumerate(observations, 1):
        packet = (root / "runtime" / f"{index:03d}.ait").read_bytes()
        frame = decoder.accept(packet)
        with Image.open(root / "runtime" / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
        history[observation["sequence"]] = {
            "observation": observation, "image": image}
        images[observation["sequence"]] = image

    calls = read(root / "calls.json")
    cursor = 0
    for call in calls:
        assert call["request"]["after"] == cursor
        assert call["reply"]["records"] == events[cursor:call["reply"]["cursor"]]
        cursor = call["reply"]["cursor"]
    assert cursor == len(events)

    attempts = read(root / "model-attempt-ledger.json")
    usage = read(root / "model-usage-ledger.json")
    assert attempts == result["model_attempt_ledger"]
    assert usage == result["model_usage_ledger"]
    assert len(attempts) == len(usage) == 2
    assert all(row["status"] == "completed" and row["usage"] == usage[index]["usage"]
               for index, row in enumerate(attempts))
    for row in usage:
        model_turn(root, row)
    fields = ("input_tokens", "cached_input_tokens",
              "cache_write_input_tokens", "output_tokens",
              "reasoning_output_tokens")
    totals = {field: sum(row["usage"][field] for row in usage)
              for field in fields}
    assert totals == result["model_usage_total"]
    assert result["model_usage_coverage"] == {field: 2 for field in fields}

    revalidation_index, recorded = next(
        (index, row) for index, row in enumerate(events)
        if row.get("event") == "receipt_target_revalidated")
    current = next(row for row in reversed(events[:revalidation_index])
                   if row.get("event") == "observation")
    previous = {sequence: item for sequence, item in history.items()
                if sequence < current["sequence"]}
    rebuilt = evaluate(result["admission"], previous, current,
                       images[current["sequence"]], recorded["checked_ns"])
    for key in ("eligible", "status", "authority_class", "point", "reason"):
        assert rebuilt[key] == recorded[key]
    assert recorded["eligible"] is False
    assert recorded["authority_class"] == "NO_TARGET_AUTHORITY"
    assert recorded["point"] is None and recorded["reason"] == reason
    buttons = [row for row in events
               if row.get("event") == "pointer_admission" and
               row.get("operation") == "button_down"]
    assert buttons == result["all_button_down_admissions"] == []
    terminal = next(row for row in events
                    if row.get("event") == "terminal" and
                    row.get("id") == "select-conveyor")
    assert terminal["status"] == "needs_decision"
    assert terminal["release"]["verified"] is True
    assert all(row["release"]["verified"] is True
               for row in events if row.get("event") == "terminal")

    initial = result["source"]["pointer_binding"]
    restored = result["restored_observation"]["pointer_binding"]
    assert restored == initial
    if condition == "binding-unavailable":
        fault_index, fault = next(
            (index, row) for index, row in enumerate(events)
            if row.get("event") == "test_focus_unbound")
        assert fault["after"]["surface"] is None
        assert current["pointer_binding"] is None
        restore = next(row for row in events
                       if row.get("event") == "test_focus_unbound_restored")
        assert restore["restored"] == initial
    else:
        fault_index, fault = next(
            (index, row) for index, row in enumerate(events)
            if row.get("event") == "test_surface_resized")
        assert fault["before"] == initial
        assert fault["after"]["surface"] == initial["surface"]
        assert fault["after"]["geometry"][2] != initial["geometry"][2]
        assert current["pointer_binding"]["geometry"] == fault["after"]["geometry"]
        restore = next(row for row in events
                       if row.get("event") == "test_surface_resize_restored")
        assert restore["restored"] == initial
    assert result["model_decision_ns"] < events[fault_index]["emitted_ns"]
    assert events[fault_index]["emitted_ns"] < current["emitted_ns"]
    assert current["capture_ns"] < recorded["checked_ns"]

    evaluation = score(read(root / "runtime/before.json"),
                       read(root / "runtime/after.json"),
                       read(HERE / "mindustry_single_tile_plan_v1.json"))
    recorded_evaluation = {key: value for key, value in
                           result["driver_evaluation"].items()
                           if key not in ("event", "emitted_ns")}
    assert evaluation == read(root / "runtime/evaluation.json")
    assert evaluation == recorded_evaluation
    assert evaluation["contract_satisfied"] is False
    assert read(root / "runtime/cleanup.json") == {
        "all_owned_processes_exited": True, "save_unchanged": True}
    assert result["bridge_exit_code"] == 0
    assert report["promotion_gate"]["passed"] is True
    return {
        "decision": report["decision"], "reason": reason,
        "authority": recorded["authority_class"], "point": recorded["point"],
        "target_button_downs": len(buttons), "binding_restored": restored == initial,
        "model_calls": len(usage), "usage": totals,
        "socket_exchanges": len(calls), "exact_frames": len(observations),
        "terminals": len([row for row in events if row.get("event") == "terminal"]),
        "timing_ms": result["timing_ms"]}


def main():
    first_feasibility = [json.loads(line) for line in
                         (FEASIBILITY1 / "runtime/events.jsonl").read_text().splitlines()]
    first_fault = next(row for row in first_feasibility
                       if row.get("event") == "test_focus_unbound")
    first_after = next(row for row in first_feasibility
                       if row.get("event") == "observation" and row.get("sequence") == 2)
    assert first_fault["after"]["surface"] is None
    assert first_after["pointer_binding"] is not None
    assert read(FEASIBILITY1 / "runtime/cleanup.json")["all_owned_processes_exited"] is True

    second_feasibility = [json.loads(line) for line in
                          (FEASIBILITY2 / "runtime/events.jsonl").read_text().splitlines()]
    second_unbound = next(row for row in second_feasibility
                          if row.get("event") == "observation" and row.get("sequence") == 2)
    second_resize_terminal = next(
        row for row in second_feasibility
        if row.get("event") == "terminal" and row.get("id") == "resize")
    assert second_unbound["pointer_binding"] is None
    assert second_resize_terminal["status"] == "failed"
    assert second_resize_terminal["error"] == "RuntimeError('test surface did not resize')"
    assert read(FEASIBILITY2 / "runtime/cleanup.json")["all_owned_processes_exited"] is True

    feasibility = read(FEASIBILITY3 / "result.json")
    assert feasibility["passed"] is True
    assert feasibility["unbound_pointer_binding"] is None
    assert feasibility["restored_focus_binding"]["geometry"] == feasibility["initial_geometry"]
    assert feasibility["resized_geometry"] != feasibility["initial_geometry"]
    assert feasibility["restored_geometry"] == feasibility["initial_geometry"]
    assert feasibility["model_calls"] == feasibility["button_downs"] == 0
    assert read(FEASIBILITY3 / "runtime/cleanup.json") == {
        "all_owned_processes_exited": True, "save_unchanged": True}

    first_error = (ATTEMPT1 / "driver-stderr.txt").read_text()
    assert "FileNotFoundError" in first_error
    assert "benchmark_discovery/benchmark_discovery" in first_error
    assert not any(ATTEMPT1.rglob("runtime"))
    assert (ATTEMPT1 / "driver-stdout.txt").read_bytes() == b""

    second_error = (ATTEMPT2 / "driver-stderr.txt").read_text()
    assert "model-palette-candidate model call failed; no retry" in second_error
    failure = read(ATTEMPT2 / "binding-unavailable/failure.json")
    assert failure["model_usage_ledger"] == []
    assert len(failure["model_attempt_ledger"]) == 1
    assert failure["model_attempt_ledger"][0]["status"] == "failed"
    assert failure["model_attempt_ledger"][0]["usage"] is None
    assert read(ATTEMPT2 / "binding-unavailable/model-palette-candidate/process.json")[
        "observed_model_identity"] is None
    assert not any(row.get("event") == "pointer_admission" and
                   row.get("operation") == "button_down"
                   for row in (json.loads(line) for line in
                   (ATTEMPT2 / "binding-unavailable/runtime/events.jsonl")
                   .read_text().splitlines()))
    assert read(ATTEMPT2 / "binding-unavailable/runtime/cleanup.json") == {
        "all_owned_processes_exited": True, "save_unchanged": True}

    prereg = read(OUT / "preregistration.json")
    for name, digest in prereg["sources"].items():
        assert sha(HERE.parent / name) == digest, name
    assert sha(HERE / prereg["prior_positive"]) == prereg["prior_positive_sha256"]
    report = read(OUT / "report.json")
    assert report["preflight"]["accepted"] is True
    assert report["preflight"]["model_calls"] == 0
    assert report["passed"] is True
    cases = {
        "binding-unavailable": audit_case(
            "binding-unavailable", "current_evidence_unavailable"),
        "surface-resized": audit_case(
            "surface-resized", "surface_size_changed")}
    fields = next(iter(cases.values()))["usage"]
    totals = {field: sum(case["usage"][field] for case in cases.values())
              for field in fields}
    audit = {
        "passed": True, "formal_block_passed": True,
        "decision": "RETAIN_RECEIPT_REVALIDATION_FOLLOWUP",
        "cases": cases,
        "totals": {
            "model_calls": sum(case["model_calls"] for case in cases.values()),
            "usage": totals,
            "socket_exchanges": sum(case["socket_exchanges"]
                                    for case in cases.values()),
            "exact_frames": sum(case["exact_frames"] for case in cases.values())},
        "retained_setup_failures": {
            "v1": "source path duplication before GUI/socket/model",
            "v2": "missing empty workspace after one GUI observation; model process failed before identity/usage"},
        "retained_feasibility": {
            "v1": "root focus was restored by the window manager before observation",
            "v2": "InputOnly focus held, direct resize was refused by maximization",
            "v3": "InputOnly unavailable binding and EWMH resize both restored"},
        "condition_retries": 0, "subagents": 0,
        "scope": prereg["scope"]}
    (OUT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
