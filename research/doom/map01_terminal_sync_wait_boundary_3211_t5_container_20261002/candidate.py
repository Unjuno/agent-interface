from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ALLOCATION = "MAP01-TERMINAL-WAIT-BOUNDARY-3211-T5-CONTAINER-20261002-01"
MAIN_SHA = "c4d2d4b1ccf4512ec79af75bd8eaecfcada39947"
T4_BLOB = "afd5d4ea1bbbede29ecb67ff49f6e944b4d22320"
RUNNER_BLOB = "f5caf71a743a563b7de046b82d44db7ebe49e829"
T4_REL = Path("research/doom/map01_terminal_sync_wait_boundary_3211_t4_20261002/candidate.py")
RUNNER_REL = Path("research/doom/map01_recovery_cover_matched_v2_runner_3211_diagnostic_v2.py")


def blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def verify_freeze(bundle: Path) -> tuple[dict, str]:
    raw = (bundle / "FREEZE.json").read_bytes()
    freeze = json.loads(raw)
    if freeze.get("main_sha") != MAIN_SHA or freeze.get("allocation_id") != ALLOCATION:
        raise ValueError("allocation/main freeze mismatch")
    for name, expected in freeze["files"].items():
        actual = hashlib.sha256((bundle / name).read_bytes()).hexdigest().upper()
        if actual != expected:
            raise ValueError(f"frozen source mismatch: {name}")
    return freeze, hashlib.sha256(raw).hexdigest()


def load_t4(repo: Path):
    t4_path = repo / T4_REL
    if blob_sha1(t4_path.read_bytes()) != T4_BLOB:
        raise ValueError("T4 candidate Git blob mismatch")
    if blob_sha1((repo / RUNNER_REL).read_bytes()) != RUNNER_BLOB:
        raise ValueError("upstream runner Git blob mismatch")
    spec = importlib.util.spec_from_file_location("frozen_t4_wait_boundary", t4_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load immutable T4 helper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    out = args.out.resolve()
    bundle = Path(__file__).resolve().parent
    freeze, freeze_sha = verify_freeze(bundle)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("candidate output namespace is not empty")
    out.mkdir(parents=True, exist_ok=True)
    t4 = load_t4(repo)
    session_cls = t4.load_session_class(repo)
    cases = [
        t4.run_case(session_cls, out, name, spec)
        for name, spec in t4.EXPECTED_CASES.items()
    ]
    receipt = {
        "schema": "map01-terminal-wait-boundary-container-candidate-v1",
        "allocation_id": ALLOCATION,
        "main_sha": MAIN_SHA,
        "candidate_source_t4_git_blob": T4_BLOB,
        "runner_git_blob": RUNNER_BLOB,
        "freeze_sha256": freeze_sha,
        "candidate_invocations": 1,
        "synthetic_child_cases": len(cases),
        "retries": 0,
        "runtime": {"python": sys.version, "platform": sys.platform},
        "image": freeze["image"],
        "cases": cases,
    }
    (out / "candidate.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
