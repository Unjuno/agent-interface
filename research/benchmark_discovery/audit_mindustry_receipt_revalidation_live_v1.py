"""Audit the retained Mindustry receipt-to-admission regression block."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_control"
sys.path.insert(0, str(LIVE))

from audit_local_visual_barrier_v1 import Decoder, Frame
from receipt_target_admission_v1 import evaluate
from mindustry_single_tile_score_v1 import score


OUT = HERE / "results/mindustry-receipt-revalidation-01"
CACHE = LIVE / "results/schema-preflight-gate-01/cache"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source(name):
    return HERE.parent / name if name.startswith("live_control/") else HERE / name


def audit_model(root, row):
    stage = row["stage"]
    result = read(root / f"{stage}-result.json")
    plan = read(root / stage / "plan.json")
    process = read(root / stage / "process.json")
    events = [json.loads(line) for line in
              (root / stage / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    turns = [event for event in events if event.get("type") == "turn.completed"]
    messages = [event for event in events if event.get("type") == "item.completed"
                and event.get("item", {}).get("type") == "agent_message"]
    assert len(turns) == len(messages) == 1
    assert turns[0]["usage"] == result["usage"] == row["usage"]
    assert json.loads(messages[0]["item"]["text"]) == result["typed"]
    assert process["exit_code"] == 0
    assert plan["requested_model"] == "gpt-5.6-luna"
    assert plan["requested_effort"] == "low"
    return result


def audit_case(condition, expected_calls, expected_frames, expected_buttons,
               expected_palette, expected_world, expected_task):
    root = OUT / condition
    report = read(root / "report.json")
    result = report["result"]
    events = [json.loads(line) for line in
              (root / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    assert len(observations) == expected_frames
    decoder = Decoder("live-control")
    images = {}
    history = {}
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((root / "runtime" / f"{index:03d}.ait").read_bytes())
        with Image.open(root / "runtime" / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
        images[observation["sequence"]] = image
        history[observation["sequence"]] = {"observation": observation, "image": image}

    calls = read(root / "calls.json")
    cursor = 0
    for call in calls:
        request, reply = call["request"], call["reply"]
        assert request["after"] == cursor
        assert reply["records"] == events[cursor:reply["cursor"]]
        cursor = reply["cursor"]
    assert cursor == len(events)

    usage = read(root / "model-usage-ledger.json")
    attempts = read(root / "model-attempt-ledger.json")
    assert usage == result["model_usage_ledger"]
    assert attempts == result["model_attempt_ledger"]
    assert len(usage) == len(attempts) == expected_calls
    assert [row["stage"] for row in usage] == [row["stage"] for row in attempts]
    assert all(row["status"] == "completed" and row["error"] is None
               and row["usage"] == usage[index]["usage"]
               for index, row in enumerate(attempts))
    for row in usage:
        audit_model(root, row)
    fields = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
              "output_tokens", "reasoning_output_tokens")
    totals = {field: sum(row["usage"][field] for row in usage) for field in fields}
    assert totals == result["model_usage_total"]
    assert result["model_usage_coverage"] == {field: expected_calls for field in fields}

    revalidations = [(index, row) for index, row in enumerate(events)
                     if row.get("event") == "receipt_target_revalidated"]
    expected_revalidations = [expected_palette] + ([] if expected_world is None
                                                    else [expected_world])
    assert len(revalidations) == len(expected_revalidations)
    intervals = []
    for (event_index, recorded), expected in zip(revalidations, expected_revalidations):
        current = next(row for row in reversed(events[:event_index])
                       if row.get("event") == "observation")
        specification = (result["palette_admission"] if recorded["id"] == "select-conveyor"
                         else result["world_admission"])
        previous = {sequence: item for sequence, item in history.items()
                    if sequence < current["sequence"]}
        rebuilt = evaluate(specification, previous, current,
                           images[current["sequence"]], recorded["checked_ns"])
        for key in ("eligible", "status", "authority_class", "point", "reason"):
            assert rebuilt[key] == recorded[key]
        assert (recorded["eligible"], recorded["reason"]) == expected
        assert current["capture_ns"] <= recorded["checked_ns"]
        buttons = [row for row in events[event_index + 1:]
                   if row.get("event") == "pointer_admission"
                   and row.get("operation") == "button_down"
                   and row.get("id") == recorded["id"]]
        if recorded["eligible"]:
            assert len(buttons) == 1
            assert recorded["checked_ns"] < buttons[0]["input_ack_ns"] < recorded["valid_until_ns"]
            intervals.append((buttons[0]["input_ack_ns"] - recorded["checked_ns"]) / 1e6)
        else:
            assert recorded["authority_class"] == "NO_TARGET_AUTHORITY"
            assert recorded["point"] is None and buttons == []

    button_ids = [row["id"] for row in events if row.get("event") == "pointer_admission"
                  and row.get("operation") == "button_down"]
    assert button_ids == expected_buttons
    terminals = [row for row in events if row.get("event") == "terminal"]
    assert all(row["status"] in ("completed", "needs_decision")
               and row["release"]["verified"] is True for row in terminals)
    if condition == "focus-unavailable":
        changed = next(row for row in events if row.get("event") == "test_focus_changed")
        restored = next(row for row in events if row.get("event") == "test_focus_restored")
        assert changed["original_focus"] == restored["focus"]
    evaluation = score(read(root / "runtime/before.json"),
                       read(root / "runtime/after.json"),
                       read(HERE / "mindustry_single_tile_plan_v1.json"))
    assert evaluation == read(root / "runtime/evaluation.json")
    assert evaluation == {key: value for key, value in result["driver_evaluation"].items()
                          if key not in ("event", "emitted_ns")}
    assert evaluation["contract_satisfied"] is expected_task
    assert result["bridge_exit_code"] == 0
    assert read(root / "runtime/cleanup.json") == {
        "all_owned_processes_exited": True, "save_unchanged": True}
    return {"formal_gate_passed": report["promotion_gate"]["passed"],
            "decision": report["decision"], "palette_revalidation": expected_palette,
            "world_revalidation": expected_world, "target_button_ids": button_ids,
            "task_success": evaluation["contract_satisfied"],
            "model_calls": expected_calls, "usage": totals,
            "socket_exchanges": result["socket_exchanges"],
            "exact_frames": len(observations), "terminals": len(terminals),
            "check_to_button_ack_ms": intervals,
            "timing_ms": result["timing_ms"]}


def main():
    preregistration = read(OUT / "preregistration.json")
    for name, digest in preregistration["sources"].items():
        assert sha(source(name)) == digest, name
    for name, digest in preregistration["preflight_cache"].items():
        assert sha(CACHE / name) == digest, name
    windows_error = (OUT / "driver-attempt-windows-stderr.txt").read_text(encoding="utf-8")
    assert "ModuleNotFoundError: No module named 'fcntl'" in windows_error
    assert (OUT / "driver-attempt-windows-stdout.txt").read_bytes() == b""
    report = read(OUT / "report.json")
    assert report["preflight"]["accepted"] is True
    assert report["preflight"]["model_calls"] == 0
    cases = {
        "positive": audit_case("positive", 4, 33,
                               ["select-conveyor", "place-one-conveyor"],
                               (True, "all_dependencies_revalidated"),
                               (True, "all_dependencies_revalidated"), True),
        "changed-palette": audit_case("changed-palette", 2, 9, [],
                                      (False, "exact_dependency_changed"), None, False),
        "changed-world": audit_case("changed-world", 4, 25, ["select-conveyor"],
                                    (True, "all_dependencies_revalidated"),
                                    (False, "stable_change_mask_changed"), False),
        "focus-unavailable": audit_case("focus-unavailable", 2, 8, [],
                                        (False, "focus_or_surface_changed"), None, False),
    }
    assert cases["positive"]["formal_gate_passed"] is True
    assert cases["changed-palette"]["formal_gate_passed"] is True
    assert cases["changed-world"]["formal_gate_passed"] is True
    assert cases["focus-unavailable"]["formal_gate_passed"] is False
    assert report["passed"] is False
    totals = {field: sum(case["usage"][field] for case in cases.values())
              for field in next(iter(cases.values()))["usage"]}
    audit = {"passed": True, "formal_block_passed": False,
             "decision": "RETAIN_RECEIPT_REVALIDATION_WITH_DIAGNOSTIC_MISMATCH",
             "failed_preregistered_check": {
                 "condition": "focus-unavailable",
                 "expected": "current_evidence_unavailable",
                 "observed": "focus_or_surface_changed",
                 "operational_authority": "NO_TARGET_AUTHORITY",
                 "target_button_downs": 0},
             "cases": cases, "totals": {"usage": totals,
                 "model_calls": sum(case["model_calls"] for case in cases.values()),
                 "socket_exchanges": sum(case["socket_exchanges"] for case in cases.values()),
                 "exact_frames": sum(case["exact_frames"] for case in cases.values())},
             "windows_launcher_attempt": "retained pre-GUI fcntl import failure; formal Linux allocation ran once",
             "subagents": 0, "retries": 0,
             "scope": preregistration["scope"]}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
