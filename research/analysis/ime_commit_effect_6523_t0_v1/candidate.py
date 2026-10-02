"""Finite synthetic route interpretation for Issue #6523 T0."""
import json
import sys
from pathlib import Path


def run(case, route):
    generation = case["target_generation"]
    phase = "UNKNOWN" if any(e["type"] == "COMPOSITION_UNKNOWN" for e in case["events"]) else "IDLE"
    value = None
    submitted = 0
    effect = None
    for event in case["events"]:
        typ = event["type"]
        current = event.get("generation") == generation
        if route == "RAW_ENTER":
            if typ == "VALUE_CHANGE" and current:
                value = event["value"]
            elif typ == "NATIVE_FILL" and current:
                value = event["value"]
            elif typ == "ENTER" and current:
                submitted += 1
            elif typ == "SUBMIT_INTENT" and current:
                submitted += 1
            elif typ == "APP_EFFECT" and current:
                effect = event["value"]
        elif route == "SYMBOLIC_ONLY":
            if typ == "VALUE_CHANGE" and current:
                value = event["value"]
            elif typ == "NATIVE_FILL" and current:
                value = event["value"]
            elif typ == "ENTER" and current:
                phase = "COMMITTED_ASSUMED"
            elif typ == "SUBMIT_INTENT" and current:
                submitted += 1
            elif typ == "APP_EFFECT" and current:
                effect = event["value"]
        elif route == "NATIVE_FILL":
            if typ == "NATIVE_FILL" and current:
                value = event["value"]
            elif typ == "VALUE_CHANGE" and current:
                value = event["value"]
            elif typ == "SUBMIT_INTENT" and current:
                submitted += 1
            elif typ == "APP_EFFECT" and current:
                effect = event["value"]
        elif route == "PHASE_AWARE":
            if not current and typ not in ("COMPOSITION_UNKNOWN",):
                continue
            if typ == "COMPOSITION_UNKNOWN":
                phase = "UNKNOWN"
            elif typ == "COMPOSITION_START":
                phase = "PREEDIT_ACTIVE"
            elif typ == "PREEDIT_UPDATE":
                if phase == "PREEDIT_ACTIVE":
                    phase = "PREEDIT_ACTIVE"
            elif typ == "COMPOSITION_CANCEL":
                phase = "CANCELLED"
            elif typ == "COMPOSITION_END":
                if phase != "UNKNOWN":
                    phase = "COMMIT_PENDING"
            elif typ in ("VALUE_CHANGE", "NATIVE_FILL"):
                value = event["value"]
                phase = "COMMITTED_VALUE_OBSERVED"
            elif typ == "SUBMIT_INTENT":
                if phase == "COMMITTED_VALUE_OBSERVED" and value is not None:
                    submitted += 1
            elif typ == "APP_EFFECT":
                effect = event["value"]
    exact_effect = (submitted > 0 and value is not None and value == case["expected"]
                    and effect == case["expected"])
    return {"case_id": case["id"], "route": route, "phase": phase,
            "committed_value": value, "submit_count": submitted,
            "effect_value": effect, "intended_value_match": value == case["expected"],
            "completion_claim": exact_effect,
            "consumer_authority": False, "consumer_side_effects": 0}


def main(cases_path, output_path):
    spec = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    rows = [run(case, route) for case in spec["cases"] for route in spec["routes"]]
    result = {"schema": "ime-commit-effect-raw-v1", "case_count": len(spec["cases"]),
              "routes": spec["routes"], "row_count": len(rows), "rows": rows}
    Path(output_path).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"schema": result["schema"], "rows": result["row_count"]}, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
