"""Probe lease-close candidate against terminal ordering on the frozen W2 fixture."""
import copy
import hashlib
import json
from pathlib import Path

from close_order_candidate import evaluate
from close_order_oracle import reconstruct


FIXTURE = Path(__file__).parents[1] / "o2-w2-independent-audit-20260928" / "trace-cases.json"
EXPECTED_FIXTURE_SHA256 = "6a693f06b1b4be15a8da35ec3aaf806d7fb3601091c8ef638c516069d1b4e95f"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    raw = FIXTURE.read_bytes()
    if digest(raw) != EXPECTED_FIXTURE_SHA256:
        raise SystemExit("STOP_FROZEN_FIXTURE_HASH_MISMATCH")
    fixture = json.loads(raw)
    frozen = next(c for c in fixture["cases"] if c["case_id"] == "release-before-terminal")

    scenarios = {
        "before_terminal": {"edge_start": 400, "edge_end": 402},
        "after_terminal": {"edge_start": 510, "edge_end": 512},
        "overlap_terminal": {"edge_start": 499, "edge_end": 501},
        "multiple_terminal_intervals": {"edge_start": 400, "edge_end": 402,
                                        "second_terminal": 300},
        "unknown_terminal_time": {"edge_start": 510, "edge_end": 512, "unknown_terminal": True},
    }
    output = {"schema": "w2-terminal-order-candidate-probe-v1",
              "disposition": "PASS_HOST_TERMINAL_BOUNDARY_CANDIDATE_ONLY",
              "fixture_sha256": EXPECTED_FIXTURE_SHA256,
              "container": False, "scenarios": {}}
    for name, spec in scenarios.items():
        case = copy.deepcopy(frozen)
        opened = next(e for e in case["events"] if e["event_type"] == "LEASE_OPEN")
        opened["lineage"]["actuation_id"] = "A4"
        edge = next(e for e in case["events"] if e.get("event_type") == "INPUT_EDGE_BRACKET"
                    and e.get("payload", {}).get("edge") == "up")
        edge["time"].update({"lower_ns": spec["edge_start"], "upper_ns": spec["edge_end"]})
        edge["payload"]["transition_interval_ns"] = [spec["edge_start"], spec["edge_end"]]
        terminal = next(e for e in case["events"] if e["event_type"] == "PROGRAM_TERMINAL")
        if spec.get("second_terminal") is not None:
            second = copy.deepcopy(terminal)
            second["event_id"] = "r5"
            second["time"] = {"lower_ns": spec["second_terminal"],
                              "upper_ns": spec["second_terminal"], "censoring": "exact"}
            case["events"].append(second)
        if spec.get("unknown_terminal"):
            terminal["time"] = {"lower_ns": None, "upper_ns": None, "censoring": "unknown"}
        else:
            terminal["time"] = {"lower_ns": 500, "upper_ns": 500, "censoring": "exact"}
        cand = evaluate(case["events"])
        oracle = reconstruct(case["events"])
        output["scenarios"][name] = {"edge_interval": [spec["edge_start"], spec["edge_end"]],
                                      "terminal_time": terminal["time"],
                                      "candidate": cand, "raw_oracle": oracle,
                                      "agree": cand == oracle}
    output["summary"] = {"scenario_count": len(scenarios),
                         "all_agree": all(x["agree"] for x in output["scenarios"].values()),
                         "expected": {"before_terminal": "AUTHORIZED_MATCH",
                                      "after_terminal": "REJECT_EDGE_AFTER_TERMINAL",
                                      "overlap_terminal": "HOLD_EDGE_TERMINAL_ORDER_UNCERTAIN",
                                      "multiple_terminal_intervals": "REJECT_EDGE_AFTER_TERMINAL",
                                      "unknown_terminal_time": "HOLD_UNKNOWN_TERMINAL_TIME"}}
    print(json.dumps(output, indent=2))
    if not output["summary"]["all_agree"]:
        raise SystemExit("FAIL_CANDIDATE_ORACLE_DISAGREEMENT")


if __name__ == "__main__":
    main()
