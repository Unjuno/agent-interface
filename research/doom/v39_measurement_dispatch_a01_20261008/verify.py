"""Verify immutable retained evidence and, optionally, an external rerun."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def check_retained():
    manifest = json.loads((HERE / "SHA256SUMS.json").read_text(encoding="utf-8"))
    for name, digest in manifest.items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
    audit = json.loads((HERE / "AUDIT.json").read_text(encoding="utf-8"))
    assert result["disposition"] == "PASS_FUTURE_DISPATCH_CONSTRUCTION_ONLY"
    assert result["modes"][0]["session"] == "session_map01_v12.py"
    assert result["modes"][1]["session"] == "session_map01_v15.py"
    assert result["modes"][0]["report_label"] == "v12_default"
    assert result["modes"][1]["report_label"] == "v15_scorer_only_per_key_release"
    assert audit["status"] == "PASS_DISPATCH_CONSTRUCTION"
    assert audit["checks_passed"] == audit["checks_total"] == 11
    assert (HERE / "normal.stdout").read_bytes() == (HERE / "optimized.stdout").read_bytes()
    return len(manifest), result, audit


def check_rerun(path, retained_result, retained_audit):
    path = path.resolve()
    assert path.is_dir() and path != HERE and HERE not in path.parents
    result = json.loads((path / "RESULT.json").read_text(encoding="utf-8"))
    audit = json.loads((path / "AUDIT.json").read_text(encoding="utf-8"))
    assert result == retained_result
    assert audit == retained_audit
    assert (path / "normal.stdout").read_bytes() == (path / "optimized.stdout").read_bytes()
    run_manifest = json.loads((path / "SHA256SUMS.json").read_text(encoding="utf-8"))
    for name, digest in run_manifest.items():
        assert hashlib.sha256((path / name).read_bytes()).hexdigest() == digest, name
    return len(run_manifest)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path,
                        help="external output directory printed by run_modes.py")
    args = parser.parse_args()
    retained_count, result, audit = check_retained()
    rerun_count = check_rerun(args.results_dir, result, audit) if args.results_dir else 0
    print(json.dumps({"verified": True, "retained_files_hashed": retained_count,
                      "rerun_files_hashed": rerun_count,
                      "disposition": result["disposition"]}, sort_keys=True))


if __name__ == "__main__":
    main()
