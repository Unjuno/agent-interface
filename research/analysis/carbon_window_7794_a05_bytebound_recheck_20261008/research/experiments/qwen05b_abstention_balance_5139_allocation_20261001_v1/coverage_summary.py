"""Report realized class/template/field counts without selecting or replacing seeds."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def template_id(row: dict) -> str:
    op = row["intent"]["op"]
    if op == "set":
        return "set_template_" + str((int(row["case_id"].split("-")[1]) // 8) % 4)
    if op == "yield":
        return "yield_" + row["intent"]["reason"]
    if op == "no_action":
        return "no_action_" + row["intent"]["reason"]
    return {"save": "save_fixed", "toggle": "toggle_fixed"}[op]


def field_id(row: dict) -> str:
    op = row["intent"]["op"]
    if op == "set":
        return row["intent"]["field"]
    if op == "save":
        return next(iter(row["state"]["staged"]))
    if op == "toggle":
        return "email_reminders"
    if op == "no_action":
        return next(iter(row["state"]["values"]))
    return "none"


def summarize(doc: dict, data_sha256: str) -> dict:
    result = {"schema": "qwen5139-realized-support-coverage-v1",
              "allocation": doc["allocation"], "formal_input_sha256": data_sha256,
              "selection_policy": "fixed preregistered seeds; realized counts reported, never used to replace seeds"}
    groups = {"support_pool": doc["support_pool"], "heldout_pool": doc["heldout_pool"],
              "heldout": doc["heldout"],
              **{"support_" + arm: rows for arm, rows in doc["supports"].items()}}
    for name, rows in groups.items():
        result[name] = {"rows": len(rows),
                        "class": dict(sorted(Counter(row["class"] for row in rows).items())),
                        "template": dict(sorted(Counter(template_id(row) for row in rows).items())),
                        "field": dict(sorted(Counter(field_id(row) for row in rows).items()))}
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    data_path, out = Path(args.data), Path(args.out)
    if out.exists():
        raise SystemExit("STOP_COVERAGE_OUTPUT_EXISTS")
    raw = data_path.read_bytes()
    doc = json.loads(raw.decode("utf-8"))
    result = summarize(doc, hashlib.sha256(raw).hexdigest())
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                      "allocation": doc["allocation"]}, sort_keys=True))


if __name__ == "__main__":
    main()
