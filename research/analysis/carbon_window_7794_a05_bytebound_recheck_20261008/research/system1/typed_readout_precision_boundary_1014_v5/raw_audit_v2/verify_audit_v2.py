"""Independent read-only verification of an audit_v2 report and its inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_RESULT_SHA = "c1a2256d8b117d7dc0ec7d90c7333f3356378313d7f735fb7aa7700278183624"
EXPECTED_CORPUS_SHA = "85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c"
EXPECTED_WEIGHTS_SHA = "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("INDEPENDENT_AUDIT_REJECT:" + message)


def verify(result_path: Path, corpus_path: Path, weights_path: Path,
           report_path: Path) -> dict:
    result_sha, corpus_sha, weights_sha = sha(result_path), sha(corpus_path), sha(weights_path)
    require(result_sha == EXPECTED_RESULT_SHA, "raw digest mismatch")
    require(corpus_sha == EXPECTED_CORPUS_SHA, "corpus digest mismatch")
    require(weights_sha == EXPECTED_WEIGHTS_SHA, "weight digest mismatch")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    require(report.get("status") == "AUDIT_PASS_RAW_ONLY", "status mismatch")
    require(report.get("errors") == [], "reported errors are not empty")
    require(report.get("rows") == 27, "row count mismatch")
    require(report.get("corruption_controls_rejected") == 5, "corruption count mismatch")
    require(report.get("result_sha256") == result_sha, "reported raw digest mismatch")
    require(report.get("corpus_sha256") == corpus_sha, "reported corpus digest mismatch")
    require(report.get("weights_sha256") == weights_sha, "reported weights digest mismatch")
    modes = report.get("modes")
    require(isinstance(modes, dict) and set(modes) == {"fp16", "bf16", "fp32"},
            "mode set mismatch")
    for name, summary in modes.items():
        require(summary.get("rows") == 9, name + " row count mismatch")
        require(summary.get("all_winners_equal") is True, name + " winner mismatch")
        require(summary.get("all_cache_isolation") is True, name + " cache-isolation mismatch")
    require(modes["fp32"].get("all_within_tolerance") is True, "FP32 tolerance summary mismatch")
    require(modes["fp16"].get("all_within_tolerance") is False, "FP16 tolerance summary mismatch")
    require(modes["bf16"].get("all_within_tolerance") is False, "BF16 tolerance summary mismatch")
    return {"status": "INDEPENDENT_AUDIT_PASS", "rows": 27,
            "corruption_controls_rejected": 5, "result_sha256": result_sha,
            "corpus_sha256": corpus_sha, "weights_sha256": weights_sha}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.result, args.corpus, args.weights, args.report), sort_keys=True))


if __name__ == "__main__":
    main()

