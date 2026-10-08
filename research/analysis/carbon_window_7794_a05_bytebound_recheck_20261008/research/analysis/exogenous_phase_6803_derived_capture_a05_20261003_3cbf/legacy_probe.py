"""Distinct four-input intervention diagnostic, NOT a replay of the A04 allocation."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

OLD = Path(__file__).resolve().parent.parent / "exogenous_opportunity_5694_matched_phase_a04_20261002"
SOURCE_SHA = "c1e39ebd99e1eee81dbac6902d6d71b03ba1deb872bec8753c22372f270c6d29"
FIXTURE_SHA = "2b3c934bef9dfdb9ea0b758521570bf8ee5d3878e2008d9b9702c9a1a371919e"


def probe(source=OLD / "candidate.py", fixture=OLD / "fixture.json"):
    source, fixture = Path(source), Path(fixture)
    hashes = {"candidate.py": hashlib.sha256(source.read_bytes()).hexdigest(),
              "fixture.json": hashlib.sha256(fixture.read_bytes()).hexdigest()}
    if hashes != {"candidate.py": SOURCE_SHA, "fixture.json": FIXTURE_SHA}:
        raise ValueError("legacy source/fixture changed")
    spec = importlib.util.spec_from_file_location("frozen_a04", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = {c["case_id"]: c for c in json.loads(fixture.read_text())["cases"]}
    rows = []
    for identity, onsets in (("c01", (9, 11)), ("c02", (11, 9))):
        for onset in onsets:
            item = copy.deepcopy(original[identity])
            item["opportunity"]["onset_ms"] = onset
            rows.append({"probe_id": f"{identity}-onset-{onset}", "input": item,
                         "output": list(module.classify(item))})
    return {"schema": "legacy-onset-probe-v1", "source_sha256": hashes, "rows": rows,
            "authority_events": 0, "live_effect_events": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = probe(args.source, args.fixture)
    with Path(args.out).open("x") as target:
        json.dump(result, target, sort_keys=True, indent=2)
        target.write("\n")
    print("LEGACY_PROBE_COMPLETE inputs=4 onset-only matched pairs=2")
