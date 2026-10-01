#!/usr/bin/env python3
"""Read-only freeze-schema adapter for the unchanged independent audit core."""
import argparse
import hashlib
import json
from pathlib import Path

import audit


def frozen_stream_hash(frozen):
    value = frozen["fixture"]["stream_sha256"]
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("missing or malformed frozen stream digest")
    int(value, 16)
    return value


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _adapt_freeze(frozen):
    """Map the preregistered nested v1 freeze into the v1 auditor's input contract."""
    sources = frozen["source_sha256"]
    adapted = dict(frozen)
    adapted["preaudit_stream_sha256"] = frozen_stream_hash(frozen)
    adapted["sealed_outcomes_sha256"] = frozen["fixture"]["sealed_outcomes_sha256"]
    adapted["run_py_sha256"] = sources["run.py"]
    adapted["runner_py_sha256"] = sources["runner.py"]
    adapted["audit_py_sha256"] = sources["audit.py"]
    return adapted


def _verify_v2_freeze(v2_freeze):
    expected = v2_freeze["sha256"]
    for name, digest in expected.items():
        if _hash(name) != digest:
            raise ValueError(f"v2 frozen identity mismatch: {name}")


def run(raw_path, output_path):
    v2_freeze = json.loads(Path("AUDIT_V2_FREEZE.json").read_text(encoding="utf-8"))
    _verify_v2_freeze(v2_freeze)
    frozen = json.loads(Path("FREEZE.json").read_text(encoding="utf-8"))
    raw = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    stream = json.loads(Path("preaudit_stream.json").read_text(encoding="utf-8"))
    outcomes = json.loads(Path("sealed_outcomes.json").read_text(encoding="utf-8"))
    adapted = _adapt_freeze(frozen)
    metrics = audit._validate(raw, stream, outcomes, adapted)
    mutations = audit._mutation_controls(raw, stream, outcomes, adapted)
    if not mutations["pass"]:
        raise ValueError("one or more frozen mutation controls were accepted")
    return {
        "schema": "issue-5764-independent-audit-v2",
        "v1_disposition": "STOP_AUDITOR_FREEZE_SCHEMA_ADAPTER",
        "candidate_raw_sha256": _hash(raw_path),
        "selection_replay": "PASS",
        "population_size": len(stream["events"]),
        "mandatory_failures": sum(bool(outcomes["outcomes"][item]["failure"])
                                   for item in raw["mandatory_event_ids"]),
        "optional_budget": stream["optional_audit_budget"],
        "metrics": metrics,
        "mutations": mutations,
        "scope": "read-only corrected freeze adapter around the independent v1 replay core; authored synthetic stream only",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.raw, args.output)
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
