"""One-shot candidate driver for registered Issue #5895 T4."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from matrix import make_matrix


ALLOCATION = "AUDIT-COMPLETION-5895-T4-ORBSTACK-20261001-01-8d0c7f53"
FROZEN = {
    "audit_formal_x11.py": ("da805fb83f70a57ad68a0768186e214524689d40",
                            "f74da3f66fa979db99c17213df31d295056b99ae04c8d8b59bd6d5b5d71a93e0"),
    "EXPECTED.json": ("3d33bda096c4c8789e183e3f864ee7626e643a7e",
                      "7bf403b88773ecdfd04243f023c17e26e859c3286b71ccf5eb2db3101e0ef076"),
    "test_audit_formal_x11.py": ("d1eb9a854cc810fa77ca173d7e2de287ee1bd64a",
                                 "1fbb4b86fec10ad8ed578efa476df1857d38e82617d802ff8e0252ff848163f5"),
}


def hashes(name: str, data: bytes) -> tuple[str, str]:
    digest = hashlib.sha256(data).hexdigest()
    blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
    expected_blob, expected_digest = FROZEN[name]
    if (blob, digest) != (expected_blob, expected_digest):
        raise SystemExit(f"frozen target source mismatch: {name}")
    return blob, digest


def prepare_output(path: Path) -> Path:
    if path.is_symlink():
        raise SystemExit("output directory must not be a symlink")
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise SystemExit("output directory must be absent or empty")
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve(strict=True)


def load_fixture_rows(target: Path) -> list[dict]:
    sys.dont_write_bytecode = True
    source = target / "test_audit_formal_x11.py"
    spec = importlib.util.spec_from_file_location("frozen_t4_fixture", source)
    if spec is None or spec.loader is None:
        raise SystemExit("frozen fixture builder unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.fixture_rows()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    target = args.target.resolve(strict=True)
    out = prepare_output(args.out)

    source_data = {name: (target / name).read_bytes() for name in FROZEN}
    source_ids = {name: hashes(name, data) for name, data in source_data.items()}
    baseline = load_fixture_rows(target)
    matrix = make_matrix(baseline)
    entries = []
    all_expected = True
    for item in matrix:
        case_id = item["case_id"]
        case_dir = out / case_id
        case_dir.mkdir()
        raw_path = case_dir / "raw.jsonl"
        audit_path = case_dir / "audit.json"
        stdout_path = case_dir / "stdout.txt"
        stderr_path = case_dir / "stderr.txt"
        raw_bytes = b"".join(
            (json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
            for row in item["rows"]
        )
        raw_path.write_bytes(raw_bytes)
        completed = subprocess.run(
            [sys.executable, "-B", str(target / "audit_formal_x11.py"), str(raw_path),
             str(target / "EXPECTED.json"), str(audit_path), "synthetic-cli"],
            cwd=target, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        )
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        all_expected &= type(completed.returncode) is int and completed.returncode == item["expected_exit"]
        entries.append({
            "case_id": case_id,
            "expected_exit": item["expected_exit"],
            "actual_exit": completed.returncode,
            "raw_path": f"{case_id}/raw.jsonl",
            "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "audit_path": f"{case_id}/audit.json",
            "audit_sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest() if audit_path.is_file() else None,
            "stdout_path": f"{case_id}/stdout.txt",
            "stdout_sha256": hashlib.sha256(stdout_path.read_bytes()).hexdigest(),
            "stderr_path": f"{case_id}/stderr.txt",
            "stderr_sha256": hashlib.sha256(stderr_path.read_bytes()).hexdigest(),
        })
    manifest = {
        "allocation": ALLOCATION,
        "disposition": "CANDIDATE_EXPECTED" if all_expected else "CANDIDATE_MISMATCH",
        "target_git_blob": source_ids["audit_formal_x11.py"][0],
        "target_sha256": source_ids["audit_formal_x11.py"][1],
        "expected_git_blob": source_ids["EXPECTED.json"][0],
        "expected_sha256": source_ids["EXPECTED.json"][1],
        "fixture_git_blob": source_ids["test_audit_formal_x11.py"][0],
        "fixture_sha256": source_ids["test_audit_formal_x11.py"][1],
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "matrix_sha256": hashlib.sha256(Path(__file__).with_name("matrix.py").read_bytes()).hexdigest(),
        "cases": entries,
    }
    (out / "candidate_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": ALLOCATION, "disposition": manifest["disposition"],
                      "case_count": len(entries), "actual_exits": [case["actual_exit"] for case in entries]},
                     sort_keys=True))
    return 0 if all_expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
