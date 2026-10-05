def main():
    #!/usr/bin/env python3
    """Independent raw JSON audit only; does not import or execute the controller."""
    import hashlib
    import json
    import sys
    from pathlib import Path

    PKG = Path(__file__).resolve().parents[1]
    TRACE_DIR = PKG / "focused-review-repaired" / "traces"
    RECEIPT = PKG / "focused-review-repaired" / "receipt.json"
    SOURCE_ROOT = PKG.parents[2]
    EXPECTED = {"hard-neutral.json", "unknown-neutral.json", "hard-unverified.json",
                "hard-keys-down.json", "hard-buttons-down.json"}

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def require(condition, message):
        if not condition:
            raise AssertionError(message)

    def index(seq, item):
        require(item in seq, f"missing timeline item: {item}")
        return seq.index(item)

    receipt = json.loads(RECEIPT.read_text())
    files = sorted(TRACE_DIR.glob("*.json"))
    require({p.name for p in files} == EXPECTED, "trace inventory changed")
    source_hashes = receipt["source_sha256"]
    fixture_path = SOURCE_ROOT / "research/doom/test_map01_overlap_controller_v39.py"
    require(sha(fixture_path) == source_hashes["research/doom/test_map01_overlap_controller_v39.py"],
            "fixture hash differs from focused-run receipt")
    controller_path = SOURCE_ROOT / "research/doom/map01_overlap_controller_v39.py"
    require(sha(controller_path) == source_hashes["research/doom/map01_overlap_controller_v39.py"],
            "controller hash differs from focused-run receipt")

    summaries = {}
    for path in files:
        data = json.loads(path.read_text())
        timeline = data["timeline"]
        require(data["pending"] is True, f"{path.name}: not a pending-future case")
        require(data["planner_calls"] == 2 if data["report"] is not None else data["planner_calls"] == 1,
                f"{path.name}: unexpected planner-call count")
        require(data["commands"][0]["op"] == "submit" and data["commands"][0]["id"] == "cover-0",
                f"{path.name}: initial cover not submitted")
        require(data["commands"][1] == {"op": "cancel", "id": "cover-0"},
                f"{path.name}: matching cover cancel missing")

        if data["report"] is None:
            require(path.name in {"hard-unverified.json", "hard-keys-down.json", "hard-buttons-down.json"},
                    f"{path.name}: unexpected absent report")
            require(len(data["barrier_events"]) == 0, f"{path.name}: barrier ran despite bad release")
            require(not any(item.startswith("begin:turn-2") or item == "frame_barrier_enter"
                            for item in timeline), f"{path.name}: replanned after bad release")
            require(data["bad_release"] in (
                {"verified": False, "keys_down": [], "buttons_down": []},
                {"verified": True, "keys_down": ["W"], "buttons_down": []},
                {"verified": True, "keys_down": [], "buttons_down": [1]}),
                f"{path.name}: bad-release case unexpected")
            summaries[path.name] = {"gate": "rejected before barrier/replan", "planner_calls": 1,
                                    "commands": [x["op"] + ":" + x.get("id", "") for x in data["commands"]],
                                    "bad_release": data["bad_release"]}
            continue

        report = data["report"]
        require(data["health_mode"] in ("hard", "unknown"), f"{path.name}: wrong health mode")
        expected_status = "HARD_INVALIDATED" if data["health_mode"] == "hard" else "UNKNOWN"
        tl = timeline
        ordered = ["planner_wait_started", "row:observation:11", "observe_invalidation_while_pending",
                   "interrupt:turn-1", "command:cancel:cover-0", "row:terminal:cover-0",
                   "planner_completed_after_interrupt", "active_answer_contract_validated",
                   "frame_barrier_enter", "frame_barrier_pass:fresh.png", "command:submit:cover-1",
                   "begin:turn-2"]
        positions = [index(tl, item) for item in ordered]
        require(positions == sorted(positions), f"{path.name}: pending/cancel/release/barrier order changed")
        require(index(tl, "row:observation:12") < index(tl, "row:terminal:cover-0"),
                f"{path.name}: overtaking frame absent before terminal")
        require(sum(item == "interrupt:turn-1" for item in tl) == 1,
                f"{path.name}: planner interrupt count changed")
        invalidation = data["barrier_events"][0]
        require(invalidation["sequence"] == 11 and invalidation["capture_ns"] == 110,
                f"{path.name}: invalidation epoch mismatch")
        require(invalidation["outcome"]["status"] == expected_status,
                f"{path.name}: expected {expected_status} outcome")
        require(invalidation["pointer_binding"]["focus"] == 7 and
                invalidation["pointer_binding"]["surface"] == 7,
                f"{path.name}: invalidation binding mismatch")
        require(report["planner_turns"] == 2 and report["planner_interruption_requests"] == 1 and
                report["policy_invalidations"] == 1 and report["model_actions_discarded"] == 1,
                f"{path.name}: report counters disagree")
        require(report["program_admissions"] == 0 and report["historical_first_executor_admissions"] == 0,
                f"{path.name}: action admission recorded")
        first, second = report["decisions"]
        require(first["model_action_discarded"] is True and
                first["discard_reason"] == "policy_dependency_invalidated" and
                first["final_action_admission"]["input_authority_admitted"] is False and
                first["final_action_admission"]["executor_admission"] is None and
                first["final_action_admission"]["grants_input_authority"] is False,
                f"{path.name}: invalidated answer retained authority")
        require(second["source_image"] == "fresh.png" and
                second["final_action_admission"]["input_authority_admitted"] is False,
                f"{path.name}: next turn did not use fresh frame/no-input terminal")
        summaries[path.name] = {
            "invalidation_status": expected_status,
            "invalidation_sequence_capture": [invalidation["sequence"], invalidation["capture_ns"]],
            "planner_turns": report["planner_turns"],
            "planner_interruptions": report["planner_interruption_requests"],
            "discarded_actions": report["model_actions_discarded"],
            "program_admissions": report["program_admissions"],
            "barrier_image": "fresh.png",
            "trace_order_pass": True,
        }

    result = {
        "scope": "independent raw JSON verification only; controller and tests were not rerun",
        "focused_receipt_exit_code": receipt["exit_code"],
        "focused_source_hashes_checked": [
            "research/doom/test_map01_overlap_controller_v39.py",
            "research/doom/map01_overlap_controller_v39.py"],
        "trace_sha256": {p.name: sha(p) for p in files},
        "cases": summaries,
        "limitations": [
            "Synthetic process, executor, planner, observations, and release receipts; no live/model/game evidence.",
            "Planner future is observed pending at invalidation, but the fake transport later returns an eligible completed answer after interrupt; controller discard is the tested gate, not real planner cancellation semantics.",
            "Health-only invalidation is triggered by a full observation row, which also updates latest. The fixture source is hash-pinned and queues wrong-binding/stale-capture frames before fresh.png; the trace timeline records only event plus sequence, not each candidate identity, so rejection details rely on the pinned fixture and returned fresh image rather than a self-contained raw candidate log.",
            "Bad-release runs abort before report serialization; their raw trace preserves one planner call, cancel, no barrier/replan, and the injected bad release, but no normal decision report."],
        "all_raw_assertions_passed": True,
    }
    out = Path(sys.argv[1]).resolve()
    with out.open("x") as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_raw_assertions_passed": True, "cases": list(summaries)}, indent=2))

if __name__ == "__main__":
    main()
