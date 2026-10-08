"""Freeze the sole candidate invocation and exact source/environment hashes."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE_REL = "research/doom/map01-v39-per-key-release-live-t0-20261004"
RUNTIME_PATHS = (
    "research/doom/session_map01_v12.py",
    "research/doom/doom_hud_signal_v1.py",
    "research/doom/doom_hud_signal_v2.py",
    "research/doom/doom_hud_signal_v3.py",
    "research/doom/doom_typed_observation_v1.py",
    "research/doom/doom_typed_release_backend_v1.py",
    "research/doom/doom_typed_release_backend_v3.py",
    "research/doom/doom_typed_coast_backend_v1.py",
    "research/live_control/coast_backend_v1.py",
    "research/live_control/executor_v3.py",
    "research/live_control/executor_v5.py",
    "research/live_control/executor_v11.py",
    "research/live_control/executor_v12.py",
    "research/live_control/input_owner_v5.py",
    "research/live_control/input_owner_v10.py",
    "research/live_control/input_transition_owner_v3.py",
    "research/live_control/lease.py",
    "research/live_control/lease_cause_v1.py",
    "research/live_control/lease_cause_v2.py",
    "research/live_control/lease_release_v1.py",
    "research/live_control/session_v8.py",
    "research/live_control/session_v9.py",
    "research/live_control/session_v10.py",
)
PACKAGE_FILES = (
    "Dockerfile", "PLAN.md", "audit.py", "candidate.py",
    "capture_environment.py", "materialize_support.py", "test_audit.py",
    "freeze_manifest.py", "ENVIRONMENT.json", "SOURCE_MANIFEST.json",
    "source-support.tar.gz",
)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--allocation-id", default=(
        "MAP01-V39-RELEASE-TELEMETRY-LIVE-59-T0-20261004-01"))
    args = parser.parse_args()
    package = ROOT / PACKAGE_REL
    runtime_hashes = {path: sha256(ROOT / path) for path in RUNTIME_PATHS}
    files = dict(runtime_hashes)
    files.update({f"{PACKAGE_REL}/{name}": sha256(package / name)
                  for name in PACKAGE_FILES})
    manifest = json.loads((package / "SOURCE_MANIFEST.json").read_text())
    environment_sha = sha256(package / "ENVIRONMENT.json")
    freeze = {
        "schema": "map01-v39-per-key-release-live-freeze-v1",
        "allocation_id": args.allocation_id,
        "source_commit": git("rev-parse", "HEAD"),
        "main_sha": args.main_sha,
        "runtime_source_paths": list(RUNTIME_PATHS),
        "runtime_sources_sha256": runtime_hashes,
        "source_support_sha256": manifest["archive_sha256"],
        "source_support_manifest_sha256": sha256(package / "SOURCE_MANIFEST.json"),
        "support_archive_path": f"{PACKAGE_REL}/source-support.tar.gz",
        "runtime_environment_path": f"{PACKAGE_REL}/ENVIRONMENT.json",
        "runtime_environment_sha256": environment_sha,
        "output_root": f"{PACKAGE_REL}/results/{args.allocation_id}",
        "programs": [
            {"id": "v39-single-space", "steps": [
                {"op": "hold", "keys": ["space"], "duration_ms": 600}]},
            {"id": "v39-two-key-up-space", "steps": [
                {"op": "hold", "keys": ["Up", "space"], "duration_ms": 600}]},
        ],
        "network_isolation": "unshare -n",
        "execution_route": "direct process in isolated OrbStack Ubuntu/arm64 guest",
        "candidate_invocations": 1,
        "auditor_invocations": "one only if candidate exit code is zero",
        "retry_policy": "no candidate retry; retain first result",
        "sha256": files,
    }
    args.out.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")


if __name__ == "__main__":
    main()
