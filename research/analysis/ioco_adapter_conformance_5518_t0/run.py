"""Execute the frozen synthetic I/O traces; never invokes a real adapter."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from contract import evaluate


ROOT = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    root = Path(args.root)
    freeze = read_json(root / "FREEZE.json")
    for relative, expected in freeze["frozen_sources"].items():
        actual = sha256(root / relative)
        if actual != expected:
            raise SystemExit(f"STOP_SOURCE_HASH_MISMATCH:{relative}:{actual}")

    spec = read_json(root / "spec.json")
    corpus = read_json(root / "cases.json")
    results = []
    by_id = {}
    for case in corpus["cases"]:
        result = evaluate(spec, case["trace"])
        row = {"case_id": case["case_id"], "implementation": case["implementation"],
               "result": result}
        results.append(row)
        by_id[case["case_id"]] = case

    direct = by_id["reference-direct"]["trace"]
    hidden = by_id["reference-hidden-batch-retry"]["trace"]
    exact_raw_equal = direct == hidden
    observable = lambda trace: [{"input": row["input"], "outputs": row["outputs"]}
                                for row in trace]
    raw = {
        "schema": "agent-interface-ioco-raw-t0-v1",
        "allocation_id": freeze["allocation_id"],
        "source_base_main_sha": freeze["base_main_sha"],
        "source_commit_sha": os.environ.get("SOURCE_COMMIT_SHA", ""),
        "freeze_sha256": sha256(root / "FREEZE.json"),
        "frozen_sources_verified": True,
        "source_sha256": {name: sha256(root / name) for name in freeze["frozen_sources"]},
        "results": results,
        "baseline": {
            "compared": ["reference-d