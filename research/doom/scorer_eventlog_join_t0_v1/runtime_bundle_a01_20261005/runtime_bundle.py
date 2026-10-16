"""Validate one co-located MAP01 runtime bundle before scorer/event joining."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from file_join import classify_files


SUMMARY_SCHEMA = "map01-independent-scorer-integration-v3"
SOURCE_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def _reject(reason):
    return {
        "decision": "POST_CANCELLATION_COOCCURRENCE",
        "reason": reason,
        "causal_attribution": False,
    }


def _read_json(path):
    with Path(path).open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if type(value) is not dict:
        raise ValueError("JSON value must be an object")
    return value


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _source_map_is_valid(value):
    return (type(value) is dict and bool(value) and
            all(isinstance(path, str) and path and
                isinstance(digest, str) and SOURCE_DIGEST.fullmatch(digest)
                for path, digest in value.items()))


def classify_run(runtime_dir, intent_id, *, max_gap_ns, source_policy, freeze):
    """Read one runtime directory and fail closed on mixed/stale metadata.

    The frozen source policy is an exact expected ``sources.json`` map. The
    summary's sample count must match the number of scorer rows read from the
    same directory before the existing interval classifier is called.
    """
    runtime = Path(runtime_dir)
    policy_path = Path(source_policy)
    freeze_path = Path(freeze)
    try:
        if not runtime.is_dir():
            return _reject("runtime_directory_missing")
        frozen = _read_json(freeze_path)
        if _sha256(policy_path) != frozen.get("expected_source_policy_sha256"):
            return _reject("source_policy_hash_mismatch")
        policy = _read_json(policy_path)
        expected = policy.get("sources")
        if policy.get("schema") != "map01-v15-source-policy-v1" or not _source_map_is_valid(expected):
            return _reject("invalid_source_policy")

        sources = _read_json(runtime / "sources.json")
        if not _source_map_is_valid(sources) or sources != expected:
            return _reject("source_manifest_mismatch")

        summary = _read_json(runtime / "scorer-summary.json")
        if (summary.get("schema") != SUMMARY_SCHEMA or
                summary.get("controller_visible") is not False or
                type(summary.get("sample_count")) is not int or
                summary["sample_count"] < 0):
            return _reject("invalid_scorer_summary")

        sample_path = runtime / "scorer-samples.jsonl"
        sample_count = sum(1 for line in sample_path.read_text(encoding="utf-8").splitlines()
                           if line.strip())
        if summary["sample_count"] != sample_count:
            return _reject("scorer_summary_sample_count_mismatch")
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        return _reject("invalid_or_missing_runtime_metadata")

    return classify_files(runtime / "events.jsonl", sample_path, intent_id,
                          max_gap_ns=max_gap_ns)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", required=True, type=Path)
    parser.add_argument("--intent-id", required=True)
    parser.add_argument("--max-gap-ns", required=True, type=int)
    parser.add_argument("--source-policy", default=Path(__file__).with_name("SOURCE_POLICY.json"), type=Path)
    parser.add_argument("--freeze", default=Path(__file__).with_name("FREEZE.json"), type=Path)
    args = parser.parse_args()
    result = classify_run(args.runtime_dir, args.intent_id, max_gap_ns=args.max_gap_ns,
                          source_policy=args.source_policy, freeze=args.freeze)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
