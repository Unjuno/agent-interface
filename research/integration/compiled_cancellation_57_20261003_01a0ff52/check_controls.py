"""Validate audit discrimination on copies; retain one source-mutation trace."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from audit import audit
from candidate import generate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    base = Path(__file__).parent
    rows = [json.loads(line) for line in args.raw.read_text().splitlines()]
    pins = {label: hashlib.sha256((base / "sources" / (label + ".py")).read_bytes()).hexdigest()
            for label in ("main", "pr6863")}
    if audit(rows, pins)["errors"]:
        raise ValueError("original raw must pass before corruption checks")
    results = []

    def control(name, mutate):
        changed = copy.deepcopy(rows)
        mutate(changed)
        result = audit(changed, pins)
        rejected = bool(result["errors"])
        results.append({"name": name, "rejected": rejected,
                        "raw_sha256": hashlib.sha256(json.dumps(changed, sort_keys=True).encode()).hexdigest(),
                        "errors": result["errors"]})

    def row_for(changed, schedule="execute:1", terminal="completed"):
        return next(row for row in changed if row["source"] == "main" and row["schedule"] == schedule and row["terminal"] == terminal)

    control("missing_row", lambda changed: changed.pop())
    control("duplicate_row", lambda changed: changed.append(copy.deepcopy(changed[0])))
    control("source_pin", lambda changed: changed[0].update(source_sha256="0" * 64))
    control("trace_order", lambda changed: row_for(changed)["trace"][0].update(order=99))
    control("removed_latch", lambda changed: row_for(changed).update(trace=[event for event in row_for(changed)["trace"] if event["event"] != "cancel_latched"]))
    control("false_cancel_check", lambda changed: next(event for event in row_for(changed)["trace"] if event["event"] == "cancel_checked" and event["value"] is True).update(value=False))
    control("prefix_count", lambda changed: row_for(changed)["receipt"].update(completed_transitions=0))
    control("lost_pending_effect", lambda changed: row_for(changed)["receipt"].update(pending_effect=None))
    control("masked_delivery_uncertain", lambda changed: row_for(changed, "never", "delivery_uncertain")["receipt"].update(reason="cancelled"))
    control("invented_success", lambda changed: row_for(changed)["receipt"].update(outcome="TASK_SUCCEEDED", reason="method_complete"))

    source = (base / "sources/main.py").read_text()
    check = '        if adapters["cancelled"]():\n            return finish("SAFE_YIELD", "cancelled")\n'
    if source.count(check) != 3:
        raise ValueError("source mutation requires exact three cancellation checks")
    mutant = source.replace(check, "")
    directory = base / "mutants"
    directory.mkdir(exist_ok=True)
    target = directory / "all_cancel_checks_removed.py"
    target.write_text(mutant)
    mutated_rows = list(generate(target, "main"))
    raw = directory / "raw.jsonl"
    raw.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in mutated_rows))
    result = audit(mutated_rows, {"main": hashlib.sha256(target.read_bytes()).hexdigest()})
    detected = sum("post_cancel_execute" in row["errors"] for row in result["errors"])
    output = {"raw_controls": results, "all_raw_controls_rejected": all(row["rejected"] for row in results),
              "implementation_mutation": {"rows": len(mutated_rows), "post_cancel_rows": detected,
                                          "source_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                                          "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
                                          "audit": result}}
    print(json.dumps(output, sort_keys=True, indent=2))
    raise SystemExit(not output["all_raw_controls_rejected"] or detected == 0)


if __name__ == "__main__":
    main()
