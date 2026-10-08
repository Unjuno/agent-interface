#!/usr/bin/env python3
"""Construction-only binding and recipient-effect mutation controls."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from candidate import decide  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text())
    policy = json.loads(args.policy.read_text())
    source = next(row for row in policy["cases"] if row["case_id"] == "matching_grant_S_RED")
    variants = {
        "source_binding": lambda row: row["proposed_action"]["provenance"].update(source_surface="source/app-X"),
        "recipient_binding": lambda row: row["proposed_action"]["provenance"].update(recipient_surface="recipient/app-C"),
        "dependency_binding": lambda row: row["proposed_action"]["provenance"].update(dependency_secret_id=None),
        "payload_effect": lambda row: row["proposed_action"].update(payload="blue"),
    }
    results = []
    for name, mutate in variants.items():
        row = copy.deepcopy(source)
        row["case_id"] = f"mutation_{name}"
        mutate(row)
        observed = decide(row, protocol)
        effect = observed["gated_effect"]
        secret_leak = bool(
            effect
            and effect.get("action_id") == row["proposed_action"]["action_id"]
            and effect.get("payload") == row["secret"]["value"]
        )
        passed = not secret_leak and effect == {
            "action_id": row["general_action"]["action_id"],
            "payload": row["general_action"]["payload"],
            "recipient_surface": row["general_action"]["recipient_surface"],
        }
        results.append({"control": name, "passed": passed, "observed": observed})
    output = {
        "control_count": len(results),
        "passed": sum(item["passed"] for item in results),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"control_count": output["control_count"], "passed": output["passed"], "output": str(args.output)}, sort_keys=True))
    if output["passed"] != output["control_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
