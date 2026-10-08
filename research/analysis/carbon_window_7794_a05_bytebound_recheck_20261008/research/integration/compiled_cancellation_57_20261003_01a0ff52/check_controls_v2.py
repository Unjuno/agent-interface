"""Construct separately labeled early-stop mutation; audit all retained controls."""
import copy
import hashlib
import json
from pathlib import Path

from audit import audit as v1
from audit_v2 import audit as v2
from candidate import generate


def main():
    base = Path(__file__).parent
    sources = base / "sources"
    pins = {label: hashlib.sha256((sources / (label + ".py")).read_bytes()).hexdigest() for label in ("main", "pr6863")}
    rows = [json.loads(line) for line in (base / "raw.jsonl").read_text().splitlines()]
    if v2(rows, pins)["errors"]:
        raise ValueError("retained original raw fails v2")
    # Reapply the same ten v1 raw corruptions under the strengthened auditor.
    # Do not repeat the prior candidate mutation: copied raw only.
    controls = []
    target = next(i for i, row in enumerate(rows) if row["source"] == "main" and row["schedule"] == "execute:1" and row["terminal"] == "completed")
    for name in ("missing_row", "duplicate_row", "source_pin", "trace_order", "removed_latch", "false_cancel_check", "prefix_count", "lost_pending_effect", "masked_delivery_uncertain", "invented_success"):
        changed = copy.deepcopy(rows)
        row = changed[target]
        if name == "missing_row": changed.pop()
        elif name == "duplicate_row": changed.append(copy.deepcopy(changed[0]))
        elif name == "source_pin": changed[0]["source_sha256"] = "0" * 64
        elif name == "trace_order": row["trace"][0]["order"] = 99
        elif name == "removed_latch": row["trace"] = [event for event in row["trace"] if event["event"] != "cancel_latched"]
        elif name == "false_cancel_check": next(event for event in row["trace"] if event["event"] == "cancel_checked" and event["value"] is True)["value"] = False
        elif name == "prefix_count": row["receipt"]["completed_transitions"] = 0
        elif name == "lost_pending_effect": row["receipt"]["pending_effect"] = None
        elif name == "masked_delivery_uncertain": next(item for item in changed if item["source"] == "main" and item["schedule"] == "never" and item["terminal"] == "delivery_uncertain")["receipt"]["reason"] = "cancelled"
        elif name == "invented_success": row["receipt"].update(outcome="TASK_SUCCEEDED", reason="method_complete")
        result = v2(changed, pins)
        controls.append({"name": name, "rejected": bool(result["errors"]), "errors": result["errors"]})
    prior_path = base / "mutants" / "raw.jsonl"
    prior = [json.loads(line) for line in prior_path.read_text().splitlines()]
    prior_result = v2(prior, {"main": prior[0]["source_sha256"]})
    target_path = base / "mutants" / "always_stop.py"
    source = (sources / "main.py").read_text()
    marker = "\n    while True:\n"
    if source.count(marker) != 1:
        raise ValueError("exact loop source required")
    target_path.write_text(source.replace(marker, '\n    return finish("SAFE_YIELD", "cancelled")\n' + marker))
    early = list(generate(target_path, "main"))
    (base / "mutants" / "always_stop.raw.jsonl").write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in early))
    early_pins = {"main": hashlib.sha256(target_path.read_bytes()).hexdigest()}
    first, second = v1(early, early_pins), v2(early, early_pins)
    output = {"raw_controls": controls, "removed_cancel_v2": prior_result,
              "always_stop_v1": first, "always_stop_v2": second,
              "disposition": "PASS_AUDIT_CONTROLS" if all(control["rejected"] for control in controls) and prior_result["errors"] and not first["errors"] and second["errors"] else "FAIL_AUDIT_CONTROLS"}
    print(json.dumps(output, sort_keys=True, indent=2))
    raise SystemExit(output["disposition"] != "PASS_AUDIT_CONTROLS")


if __name__ == "__main__":
    main()
