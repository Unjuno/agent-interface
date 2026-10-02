"""Conservative route certificate candidate for Issue #6059 T0."""
import argparse
import json
from pathlib import Path


def classify(case):
    deadline = case["deadline"]
    stages = case["stages"]
    if case.get("assumptions_valid", True) is not True:
        return "UNKNOWN_ASSUMPTION_VIOLATED", None
    if case.get("shared_resource_interference"):
        return "UNKNOWN_SHARED_RESOURCE_CONTENTION", None

    upper_total = 0
    bounded_uppers = []
    for stage in stages:
        if stage.get("unbounded"):
            timeout = stage.get("timeout")
            cancel = stage.get("cancellation_upper")
            if not stage.get("typed_terminal") or not isinstance(timeout, int) or not isinstance(cancel, int) or timeout < 0 or cancel < 0:
                return "UNKNOWN_UNBOUNDED_STAGE", None
            upper_total += timeout + cancel
            continue
        if stage.get("guarantee") != "proven":
            return "UNKNOWN_NO_SERVICE_GUARANTEE", None
        lower, upper = stage.get("lower"), stage.get("upper")
        if not isinstance(lower, int) or not isinstance(upper, int) or lower < 0 or upper < lower:
            return "UNKNOWN_INVALID_SERVICE_ENVELOPE", None
        upper_total += upper
        bounded_uppers.append(upper)

    # Two simultaneous FIFO jobs on two serial queues: target B completes at
    # A1 + max(B1, A2) + B2. Each queue's upper service bound applies twice.
    if case.get("queue_topology") == "two_queue_fifo_burst":
        if len(bounded_uppers) != 2:
            return "UNKNOWN_INVALID_TOPOLOGY", None
        upper_total = bounded_uppers[0] + max(bounded_uppers[0], bounded_uppers[1]) + bounded_uppers[1]

    lower_bound = case.get("sound_lower_bound")
    if (isinstance(lower_bound, dict)
            and lower_bound.get("source") == "independent_proof"
            and isinstance(lower_bound.get("ticks"), int)
            and lower_bound["ticks"] > deadline):
        return "CERTIFIED_DEADLINE_IMPOSSIBLE", {"lower_ticks": lower_bound["ticks"]}
    if upper_total <= deadline:
        return "CERTIFIED_DEADLINE_MET", {"upper_ticks": upper_total}
    return "UNKNOWN_UPPER_BOUND_EXCEEDS_DEADLINE", {"upper_ticks": upper_total}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    rows = []
    for case in data["scenarios"]:
        label, bound = classify(case)
        rows.append({"id": case["id"], "label": label, "bound": bound})
    Path(args.output).write_text(json.dumps({"allocation_id": data["allocation_id"], "certificates": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"candidate complete: {len(rows)} certificates")


if __name__ == "__main__":
    main()
