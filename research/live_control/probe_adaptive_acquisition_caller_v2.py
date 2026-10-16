"""Offline retained-record coverage for typed local execution yields."""
import hashlib
import json
from pathlib import Path

from adaptive_acquisition_caller_v2 import ModelFailure, run


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/adaptive-acquisition-caller-02"
ANCHOR = HERE / "results/openttd-anchor-first-live-01/report.json"
RECOVERY = HERE / "results/openttd-wrong-anchor-recovery-live-02/report.json"
NO_MATCH = HERE / "results/openttd-evidence-authority-pair-02/no-match/report.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Clock:
    def __init__(self):
        self.value = 1_000_000

    def __call__(self):
        self.value += 100
        return self.value


def model(label, archived, output, *, usage=None, call_id=None):
    archived_usage = archived["usage"] if usage is None else usage
    return lambda payload: {
        "call_id": call_id or "retained:" + label,
        "output": output, "usage": archived_usage,
        "requested_model": "gpt-5.6-luna",
        "requested_effort": "low", "cost": None}


def spec(route="cold", origin="model_produced", provided=None, cached=None,
         repair_on=None):
    return {"target": "OpenTTD Company Finances", "route": route,
            "coarse_origin": origin, "provided_coarse": provided,
            "cached_target": cached, "repair_on": repair_on or [],
            "session_id": "offline-retained-records"}


TARGET = {"point": [506, 79], "receipt": "finance",
          "authority": "reference_only"}
COARSE = {"status": "candidate", "point": [505, 79]}
ANCHOR_ACCEPT = {"status": "target_reference", "target": TARGET}
ANCHOR_EXPAND = {"status": "expand_search", "anchor": [456, 79]}
EXPANDED_ACCEPT = {"status": "target_reference", "target": TARGET}


def adapters(models=None, *, reuse={"status": "revalidated"},
             final={"status": "revalidated"},
             execute={"status": "completed"}, events=None, calls=None):
    events = events if events is not None else []
    calls = calls if calls is not None else []
    values = {
        "observe_source": {"frame": "retained-source"},
        "acquire_anchor": {"receipt": "anchor"},
        "reuse_revalidate": reuse,
        "acquire_expansion": {"receipts": 5},
        "final_revalidate": final,
        "execute": execute,
        "verify_effect": {"status": "succeeded"}}
    result = {"journal": lambda event: events.append(event)}
    for name, value in values.items():
        def local(payload, stage=name, answer=value):
            calls.append(stage)
            return answer
        result[name] = local
    for name, function in (models or {}).items():
        def wrapped(payload, stage=name, adapter=function):
            calls.append(stage)
            return adapter(payload)
        result[name] = wrapped
    return result


def main():
    anchor_report = read(ANCHOR)["result"]
    recovery_report = read(RECOVERY)["result"]
    no_match_report = read(NO_MATCH)["result"]
    coarse_record = anchor_report["candidate_model"]
    anchor_accept_record = anchor_report["anchor_model"]
    anchor_expand_record = recovery_report["anchor_model"]
    expanded_record = recovery_report["selection_model"]
    no_match_anchor_record = no_match_report["anchor_model"]
    no_match_expanded_record = no_match_report["selection_model"]
    retained = {
        "anchor_report": {"path": str(ANCHOR.relative_to(HERE)),
                          "sha256": sha(ANCHOR)},
        "recovery_report": {"path": str(RECOVERY.relative_to(HERE)),
                            "sha256": sha(RECOVERY)},
        "no_match_report": {"path": str(NO_MATCH.relative_to(HERE)),
                            "sha256": sha(NO_MATCH)}}
    scenarios = {}

    events = []; calls = []
    scenarios["cold-anchor-accepted"] = run(spec(), adapters({
        "coarse_model": model("coarse", coarse_record, COARSE),
        "anchor_model": model("anchor-accept", anchor_accept_record,
                              ANCHOR_ACCEPT)}, events=events, calls=calls),
        clock=Clock(), id_factory=iter(["a1", "a2"]).__next__)
    assert scenarios["cold-anchor-accepted"]["outcome"] == "TASK_SUCCEEDED"
    assert scenarios["cold-anchor-accepted"]["accounting"]["attempted_calls"] == 2
    assert scenarios["cold-anchor-accepted"]["accounting"]["usage_totals"][
        "input_tokens"] == 17_386
    accepted_events = events
    assert [row["event"] for row in accepted_events
            if row["event"].startswith("model_attempt_")] == [
                "model_attempt_started", "model_attempt_finished",
                "model_attempt_started", "model_attempt_finished"]

    events = []; calls = []
    scenarios["cold-expanded-recovery"] = run(spec(), adapters({
        "coarse_model": model("coarse-expanded", coarse_record, COARSE),
        "anchor_model": model("anchor-expand", anchor_expand_record,
                              ANCHOR_EXPAND),
        "expanded_model": model("expanded", expanded_record,
                                EXPANDED_ACCEPT)}, events=events, calls=calls),
        clock=Clock(), id_factory=iter(["e1", "e2", "e3"]).__next__)
    expanded = scenarios["cold-expanded-recovery"]
    assert expanded["outcome"] == "TASK_SUCCEEDED"
    assert expanded["accounting"]["attempted_calls"] == 3
    assert expanded["accounting"]["usage_totals"]["input_tokens"] == 25_675
    assert expanded["comparison"]["class"] == "full_cold"
    expanded_events = events
    assert len([row for row in expanded_events
                if row["event"] == "model_attempt_started"]) == 3

    scenarios["injected-expanded-subpath"] = run(
        spec(origin="injected_archive", provided={"point": [456, 79]}),
        adapters({
            "anchor_model": model("injected-anchor", anchor_expand_record,
                                  ANCHOR_EXPAND),
            "expanded_model": model("injected-expanded", expanded_record,
                                    EXPANDED_ACCEPT)}),
        clock=Clock(), id_factory=iter(["i1", "i2"]).__next__)
    injected = scenarios["injected-expanded-subpath"]
    assert injected["accounting"]["usage_totals"]["input_tokens"] == 16_387
    assert injected["comparison"] == {
        "class": "injected_subpath", "omitted_stages": ["coarse_model"],
        "comparable_to_full_cold": False}

    no_match = {"status": "no_match"}
    no_match_calls = []
    scenarios["cold-no-match"] = run(spec(), adapters({
        "coarse_model": model("coarse-no-match", coarse_record, COARSE),
        "anchor_model": model("no-match-anchor", no_match_anchor_record,
                              ANCHOR_EXPAND),
        "expanded_model": model("no-match-expanded", no_match_expanded_record,
                                no_match)}, calls=no_match_calls),
        clock=Clock(), id_factory=iter(["n1", "n2", "n3"]).__next__)
    assert scenarios["cold-no-match"]["outcome"] == "SAFE_STOP"
    assert scenarios["cold-no-match"]["reason"] == "no_match"
    assert "execute" not in no_match_calls

    scenarios["cold-search-exhausted"] = run(spec(), adapters({
        "coarse_model": model("coarse-exhaust", coarse_record, COARSE),
        "anchor_model": model("anchor-exhaust", anchor_expand_record,
                              ANCHOR_EXPAND),
        "expanded_model": model("expanded-exhaust", expanded_record,
                                {"status": "search_exhausted"})}),
        clock=Clock(), id_factory=iter(["x1", "x2", "x3"]).__next__)
    assert scenarios["cold-search-exhausted"]["reason"] == "search_exhausted"

    for name, status in (("cold-stale-refusal", "stale"),
                         ("cold-association-refusal", "association_changed")):
        local_calls = []
        scenarios[name] = run(spec(), adapters({
            "coarse_model": model(name + "-coarse", coarse_record, COARSE),
            "anchor_model": model(name + "-anchor", anchor_accept_record,
                                  ANCHOR_ACCEPT)},
            final={"status": status}, calls=local_calls),
            clock=Clock(), id_factory=iter([name + "1", name + "2"]).__next__)
        assert scenarios[name]["outcome"] == "SAFE_STOP"
        assert scenarios[name]["reason"] == status and "execute" not in local_calls

    scenarios["warm-reuse"] = run(
        spec(route="reuse", origin="caller_provided", cached=TARGET),
        adapters(), clock=Clock())
    warm = scenarios["warm-reuse"]
    assert warm["outcome"] == "TASK_SUCCEEDED"
    assert warm["accounting"]["attempted_calls"] == 0
    assert warm["accounting"]["usage_totals"]["input_tokens"] == 0
    assert warm["comparison"]["class"] == "warm_reuse"

    repair_calls = []
    scenarios["warm-invalidate-repair"] = run(
        spec(route="reuse", origin="caller_provided", cached=TARGET,
             repair_on=["association_changed"]),
        adapters({"expanded_model": model(
            "warm-repair", expanded_record, EXPANDED_ACCEPT)},
            reuse={"status": "association_changed"}, calls=repair_calls),
        clock=Clock(), id_factory=iter(["r1"]).__next__)
    repaired = scenarios["warm-invalidate-repair"]
    assert repaired["outcome"] == "TASK_SUCCEEDED"
    assert repaired["accounting"]["attempted_calls"] == 1
    assert repaired["accounting"]["usage_totals"]["input_tokens"] == 8_280
    assert repair_calls.index("reuse_revalidate") < repair_calls.index(
        "acquire_expansion") < repair_calls.index("expanded_model")

    refuse_calls = []
    scenarios["warm-association-refusal"] = run(
        spec(route="reuse", origin="caller_provided", cached=TARGET),
        adapters(reuse={"status": "association_changed"}, calls=refuse_calls),
        clock=Clock())
    assert scenarios["warm-association-refusal"]["outcome"] == "SAFE_STOP"
    assert "execute" not in refuse_calls and "expanded_model" not in refuse_calls

    uncertain_calls = []
    scenarios["execution-delivery-uncertain"] = run(spec(), adapters({
        "coarse_model": model("uncertain-coarse", coarse_record, COARSE),
        "anchor_model": model("uncertain-anchor", anchor_accept_record,
                              ANCHOR_ACCEPT)},
        execute={"status": "delivery_uncertain"}, calls=uncertain_calls),
        clock=Clock(), id_factory=iter(["u1", "u2"]).__next__)
    uncertain = scenarios["execution-delivery-uncertain"]
    assert uncertain["outcome"] == "EXECUTION_INCOMPLETE"
    assert uncertain["delivery"] == "delivery_uncertain"
    assert uncertain["input_authority"] == "consumed_by_recorded_execute_stage"
    assert uncertain["execution_progress"] == {"status": "delivery_uncertain"}
    assert "verify_effect" not in uncertain_calls

    partial_calls = []
    scenarios["execution-local-safe-yield-after-action"] = run(spec(), adapters({
        "coarse_model": model("yield-coarse", coarse_record, COARSE),
        "anchor_model": model("yield-anchor", anchor_accept_record,
                              ANCHOR_ACCEPT)},
        execute={"status": "safe_yield", "reason": "unknown_state",
                 "completed_actions": 1}, calls=partial_calls),
        clock=Clock(), id_factory=iter(["y1", "y2"]).__next__)
    partial_yield = scenarios["execution-local-safe-yield-after-action"]
    assert partial_yield["outcome"] == "EXECUTION_INCOMPLETE"
    assert partial_yield["reason"] == "unknown_state"
    assert partial_yield["delivery"] == "confirmed_partial"
    assert partial_yield["execution_progress"] == {
        "status": "safe_yield", "reason": "unknown_state",
        "completed_actions": 1}
    assert partial_yield["input_authority"] == (
        "consumed_by_recorded_execute_stage")
    assert partial_yield["accounting"] == uncertain["accounting"]
    assert "verify_effect" not in partial_calls

    no_action_calls = []
    scenarios["execution-local-safe-yield-before-action"] = run(spec(), adapters({
        "coarse_model": model("zero-coarse", coarse_record, COARSE),
        "anchor_model": model("zero-anchor", anchor_accept_record,
                              ANCHOR_ACCEPT)},
        execute={"status": "safe_yield", "reason": "missing_symbol",
                 "completed_actions": 0}, calls=no_action_calls),
        clock=Clock(), id_factory=iter(["z1", "z2"]).__next__)
    no_action = scenarios["execution-local-safe-yield-before-action"]
    assert no_action["reason"] == "missing_symbol"
    assert no_action["delivery"] == "not_attempted"
    assert no_action["input_authority"] == "none"
    assert "verify_effect" not in no_action_calls

    scenarios["execution-invalid-yield-reason"] = run(spec(), adapters({
        "coarse_model": model("bad-coarse", coarse_record, COARSE),
        "anchor_model": model("bad-anchor", anchor_accept_record,
                              ANCHOR_ACCEPT)},
        execute={"status": "safe_yield", "reason": "invented_reason",
                 "completed_actions": 1}),
        clock=Clock(), id_factory=iter(["b1", "b2"]).__next__)
    invalid_yield = scenarios["execution-invalid-yield-reason"]
    assert invalid_yield["outcome"] == "CALLER_FAILED"
    assert "unsupported local execution yield reason" in invalid_yield["reason"]

    def failed(payload):
        raise ModelFailure("retained unavailable usage", call_id="failed:1")
    scenarios["model-failure-missing-usage"] = run(
        spec(), adapters({"coarse_model": failed}), clock=Clock(),
        id_factory=iter(["f1"]).__next__)
    failed_result = scenarios["model-failure-missing-usage"]
    assert failed_result["outcome"] == "CALLER_FAILED"
    assert failed_result["accounting"]["attempted_calls"] == 1
    assert failed_result["accounting"]["completed_calls"] == 0
    assert all(value is None for value in
               failed_result["accounting"]["usage_totals"].values())

    def failed_with_usage(payload):
        raise ModelFailure("retained usage on failed call", call_id="failed:usage",
                           usage=coarse_record["usage"])
    scenarios["model-failure-available-usage"] = run(
        spec(), adapters({"coarse_model": failed_with_usage}), clock=Clock(),
        id_factory=iter(["fu1"]).__next__)
    failed_usage = scenarios["model-failure-available-usage"]
    assert failed_usage["outcome"] == "CALLER_FAILED"
    assert failed_usage["accounting"]["completed_calls"] == 0
    assert failed_usage["accounting"]["usage_totals"] == coarse_record["usage"]

    incomplete_usage = {"input_tokens": 9288, "output_tokens": 390,
                        "reasoning_output_tokens": 310}
    scenarios["completed-missing-usage-field"] = run(spec(), adapters({
        "coarse_model": model("partial", coarse_record, COARSE,
                              usage=incomplete_usage),
        "anchor_model": model("partial-anchor", anchor_accept_record,
                              ANCHOR_ACCEPT)}),
        clock=Clock(), id_factory=iter(["p1", "p2"]).__next__)
    partial = scenarios["completed-missing-usage-field"]["accounting"]
    assert partial["usage_totals"]["input_tokens"] == 17_386
    assert partial["usage_totals"]["cached_input_tokens"] is None

    scenarios["duplicate-call-id"] = run(spec(), adapters({
        "coarse_model": model("duplicate-coarse", coarse_record, COARSE,
                              call_id="duplicate"),
        "anchor_model": model("duplicate-anchor", anchor_accept_record,
                              ANCHOR_ACCEPT, call_id="duplicate")}),
        clock=Clock(), id_factory=iter(["d1", "d2"]).__next__)
    assert scenarios["duplicate-call-id"]["accounting"][
        "duplicate_call_ids"] == ["duplicate"]

    report = {"passed": True, "retained_sources": retained,
              "journal_samples": {
                  "cold-anchor-accepted": accepted_events,
                  "cold-expanded-recovery": expanded_events},
              "scenarios": scenarios,
              "scope": ("offline accounting and branch mechanics using retained "
                        "usage plus test doubles; no new model, GUI, task efficacy, "
                        "latency, portability or token-saving claim")}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print("adaptive_acquisition_caller_v2_probe_passed")


if __name__ == "__main__":
    main()
