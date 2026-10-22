#!/usr/bin/env python3
"""One-shot diagnostic of the frozen A01 checker on baseline and mutations."""

import argparse
import copy
import importlib.util
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--legacy-audit", required=True)
    parser.add_argument("--saved-audit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    if out.exists():
        raise SystemExit("refusing to overwrite output")
    spec = importlib.util.spec_from_file_location("frozen_a01_audit", args.legacy_audit)
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    fixture = json.loads(Path(args.fixture).read_text())
    raw = json.loads(Path(args.candidate).read_text())

    unsupported = copy.deepcopy(raw)
    branches = next(r for r in unsupported["cases"] if r["case_id"] == "spurious_loss_safe_separator")["cegar"]["policy"]["branches"]
    branches[0]["observation"] = ["secret-a"]
    branches[1]["observation"] = ["secret-b"]

    swapped = copy.deepcopy(raw)
    branches = next(r for r in swapped["cases"] if r["case_id"] == "spurious_loss_safe_separator")["cegar"]["policy"]["branches"]
    branches[0]["policy"], branches[1]["policy"] = branches[1]["policy"], branches[0]["policy"]

    results = {"unchanged": legacy.validate(fixture, raw),
               "unsupported_observation_values": legacy.validate(fixture, unsupported),
               "swapped_observation_routes": legacy.validate(fixture, swapped)}
    saved = json.loads(Path(args.saved_audit).read_text())
    baseline_matches_saved = results["unchanged"] == saved
    passed = (results["unchanged"]["passed"] and
              baseline_matches_saved and
              results["unsupported_observation_values"]["passed"] and
              results["swapped_observation_routes"]["passed"])
    result = {"schema": "issue8553-a03-legacy-probe-v1", "passed": passed,
              "baseline_matches_saved_audit": baseline_matches_saved, "results": results,
              "interpretation": "legacy checker accepts both diagnostic mutations" if passed else
                  "legacy checker did not reproduce both accepted mutations"}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("legacy-gap-reproduced" if passed else "legacy-gap-not-reproduced")
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
