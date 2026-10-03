"""Post-result custody and result-corruption construction, no scientific replay."""
import argparse
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

import intervals


def demand(value, message):
    if not value:
        raise RuntimeError(message)


def checker(path):
    spec = importlib.util.spec_from_file_location("private_interval_checker", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rejected(call):
    try:
        call()
    except (ValueError, KeyError, OSError, TypeError):
        return True
    return False


def main():
    p = argparse.ArgumentParser()
    for name in ("inputs", "manifest", "freeze", "result", "checker"):
        p.add_argument(name, type=Path)
    args = p.parse_args()
    freeze = json.loads(args.freeze.read_bytes())
    selected = intervals.verify_inputs(args.inputs, args.manifest, freeze)
    original = intervals.strict_load(selected[intervals.A02 + "FREEZE.json"])
    sums = selected[intervals.A02 + "results/formal-a02/SHA256SUMS.txt"].decode().splitlines()
    lookup = {}
    for line in sums:
        digest, path = line.split(maxsplit=1)
        demand(path not in lookup, "duplicate-original-manifest-path")
        lookup[path] = digest
    matched = 0
    for path, content in selected.items():
        if path.startswith(intervals.A02 + "results/formal-a02/") and not path.endswith("SHA256SUMS.txt"):
            demand(lookup[path] == hashlib.sha256(content).hexdigest(), "original-artifact-sha256")
            matched += 1
    for name in ("fixture.py", "candidate.py"):
        demand(hashlib.sha256(selected[intervals.A02 + name]).hexdigest() == original["source_sha256"][name],
               "original-source-sha256")
    demand(hashlib.sha256(selected[intervals.RAW + "formal-trials.json"]).hexdigest() ==
           original["allocation_plan"]["input_sha256"], "original-plan-input-sha256")
    custody = []
    with tempfile.TemporaryDirectory(prefix="interval-custody-", dir=args.inputs.parent) as temp:
        scratch = Path(temp)
        copied = scratch / "inputs"
        shutil.copytree(args.inputs, copied)
        for path in (intervals.A02 + "fixture.py", intervals.RAW + "app-events.jsonl",
                     intervals.RAW + "effect-b05-sensitive-screenshot.json"):
            changed = copied / path
            original_bytes = changed.read_bytes()
            changed.write_bytes(original_bytes + b"\n")
            outcome = rejected(lambda: intervals.verify_inputs(copied, args.manifest, freeze))
            custody.append({"name": "changed-input-bytes:" + path, "rejected": outcome})
            demand(outcome, "accepted-changed-input")
            changed.write_bytes(original_bytes)
        for name, alter in (
            ("wrong-source-identity", lambda m: m.update(source_commit="0" * 40)),
            ("wrong-mode", lambda m: m["files"][0].update(mode="120000")),
            ("wrong-blob", lambda m: m["files"][0].update(git_blob="0" * 40)),
            ("wrong-byte-count", lambda m: m["files"][0].update(bytes=m["files"][0]["bytes"] + 1)),
            ("path-escape", lambda m: m["files"][0].update(path="../outside")),
        ):
            metadata = json.loads(args.manifest.read_bytes())
            alter(metadata)
            damaged_manifest = scratch / "damaged-manifest.json"
            damaged_manifest.write_text(json.dumps(metadata), encoding="utf-8")
            damaged_freeze = dict(freeze, input_manifest_sha256=hashlib.sha256(damaged_manifest.read_bytes()).hexdigest())
            outcome = rejected(lambda: intervals.verify_inputs(copied, damaged_manifest, damaged_freeze))
            custody.append({"name": name, "rejected": outcome})
            demand(outcome, "accepted-manifest-corruption")
        auditor = checker(args.checker)
        result_cases = []
        for name, alter in (
            ("wrong-row-label", lambda r: r["rows"][0].update(label="WRONG")),
            ("wrong-lower-reading", lambda r: r["rows"][0].update(lower_ns=r["rows"][0]["lower_ns"] + 1)),
            ("wrong-cell-bound", lambda r: r["cells"]["SENSITIVE/MINIMAL"].update(miss_count_bounds=[0, 1])),
            ("wrong-scientific-disposition", lambda r: r.update(scientific_disposition="PASS")),
            ("boolean-zero-cell", lambda r: r["cells"]["SENSITIVE/MINIMAL"].update(late=False)),
            ("float-lower-reading", lambda r: r["rows"][0].update(lower_ns=float(r["rows"][0]["lower_ns"]))),
            ("wrong-result-trial-count", lambda r: r.update(trial_count=179)),
        ):
            result = json.loads(args.result.read_bytes())
            alter(result)
            damaged_result = scratch / "damaged-result.json"
            damaged_result.write_text(json.dumps(result), encoding="utf-8")
            outcome = rejected(lambda: auditor.check(args.inputs, args.manifest, args.freeze, damaged_result))
            result_cases.append({"name": name, "rejected": outcome})
    print(json.dumps({"original_manifest_selected_matches": matched, "custody_corruptions": custody,
                      "result_corruptions": result_cases,
                      "checker_sha256": hashlib.sha256(args.checker.read_bytes()).hexdigest(),
                      "accepted_result_corruption_count": sum(not r["rejected"] for r in result_cases)}, sort_keys=True))


if __name__ == "__main__":
    main()
