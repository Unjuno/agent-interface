"""Deterministic synthetic context-arm generator for Issue #8313 T0."""
import hashlib
import json
import sys
from pathlib import Path


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value).hexdigest()


def build(fixture_bytes):
    fixture = json.loads(fixture_bytes)
    rows = []
    for condition in fixture["conditions"]:
        for depth in fixture["conflict_depths"]:
            history = [{"id": f"OLD_{i+1}", "value": f"TARGET_OLD_{i+1}", "status": "SUPERSEDED"} for i in range(depth)]
            baseline = {"id": "BASELINE", "value": condition.get("baseline_value", "TARGET_A"), "status": "OBSERVED"}
            current = {"id": "CURRENT", "value": condition["final_value"], "status": "OBSERVED"}
            for arm in fixture["arms"]:
                if arm == "CURRENT_ONLY":
                    episodes = []
                    ledger = []
                    padding = " " * (depth * 128 - 2 if depth else 0)
                elif arm == "FULL_CONFLICTING_HISTORY":
                    episodes = history
                    ledger = []
                    padding = " " * max(0, depth * 128 - len(canonical(episodes)))
                elif arm == "NONCONFLICTING_HISTORY":
                    episodes = [{"id": f"PAD_{i+1}", "value": f"UNRELATED_{i+1}", "status": "OBSERVED"} for i in range(depth)]
                    ledger = []
                    padding = " " * max(0, depth * 128 - len(canonical(episodes)))
                else:
                    episodes = []
                    ledger = [{"source_id": item["id"], "prior_value": item["value"], "current_id": "CURRENT", "status": "SUPERSEDED"} for item in history]
                    padding = " " * max(0, depth * 128 - len(canonical(ledger)))
                body = {
                    "task": "Identify the current object; answer the requested current value or baseline-to-current change.",
                    "query": condition["query"],
                    "authority": fixture["authority"],
                    "baseline": baseline if condition["kind"] == "history_required" else None,
                    "episodes": episodes,
                    "ledger": ledger,
                    "padding": padding,
                    "current": current,
                }
                serialized = canonical(body)
                cue = serialized.encode("utf-8").find(b'"current"')
                rows.append({
                    "condition_id": condition["id"], "kind": condition["kind"], "depth": depth,
                    "arm": arm, "body": body, "current_cue_byte_offset": cue,
                    "utf8_bytes": len(serialized.encode("utf-8")),
                    "body_sha256": digest(serialized.encode("utf-8")),
                    "expected": condition["expected"],
                    "expected_information": "baseline_and_current" if condition["kind"] == "history_required" else "current_only",
                })
    pos_a = '{"padding":"","task":"position control","current":{"id":"CURRENT","value":"TARGET_Z"}}'
    pos_b = '{"task":"position control","padding":"' + (' ' * 80) + '","current":{"id":"CURRENT","value":"TARGET_Z"}}'
    return {
        "schema_version": 1, "allocation_id": fixture["allocation_id"],
        "fixture_sha256": digest(fixture_bytes), "rows": rows,
        "position_control": {"id": fixture["position_control"]["id"], "before_sha256": digest(pos_a.encode()), "after_sha256": digest(pos_b.encode()), "offset_differs": pos_a.encode().find(b'"current"') != pos_b.encode().find(b'"current"')},
    }


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py FIXTURE OUTPUT")
    fixture_path, output_path = map(Path, sys.argv[1:])
    raw = build(fixture_path.read_bytes())
    with output_path.open("x", encoding="utf-8") as stream:
        json.dump(raw, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
