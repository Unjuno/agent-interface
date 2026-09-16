"""Build a deterministic Agent Interface Research Preview archive from a clean Git RC.

The archive intentionally contains the complete tracked source closure at HEAD. This is
larger than a hand-pruned runtime bundle, but avoids silently omitting retained evidence
or runtime source files required by audit-retained.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

CHANNEL = "Research Preview"
RELEASE_DATE = "2026-09-17"
REQUIRED_TRACKED = (
    "runtime/golden-demo-v3.sh",
    "runtime/setup-golden-demo-v3.sh",
    "runtime/golden_desktop_demo_v3.py",
    "runtime/requirements-golden.txt",
    "release/first_run_smoke_v1/preflight.py",
    "release/preview_bundle_v1/QUICKSTART.md",
    "release/preview_bundle_v1/SUPPORT.md",
    "release/preview_bundle_v1/RELEASE_NOTES.md",
    "release/preview_bundle_v1/accept_supported_host.py",
    "research/live_control/results/integrated-efficiency-live-01/preregistration.json",
    "research/live_control/results/integrated-efficiency-live-01/report.json",
    "research/live_control/results/integrated-efficiency-live-01/audit.json",
)


class BuildError(RuntimeError):
    pass


def _git(root: Path, *args: str, binary: bool = False) -> str | bytes:
    try:
        out = subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.STDOUT)
    except (OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, "output", b"")
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", "replace")
        raise BuildError(f"git {' '.join(args)} failed: {detail}") from error
    return out if binary else out.decode("utf-8").strip()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inspect_rc(root: Path) -> dict:
    root = root.resolve()
    if not (root / ".git").exists():
        raise BuildError("build must run from a Git checkout; extracted archives are verification targets, not build inputs")
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise BuildError("release build requires a clean checkout; dirty paths:\n" + str(status))
    head = str(_git(root, "rev-parse", "--verify", "HEAD"))
    short = str(_git(root, "rev-parse", "--short=12", "HEAD"))
    commit_time = str(_git(root, "show", "-s", "--format=%cI", "HEAD"))
    tracked = bytes(_git(root, "ls-files", "-z", binary=True)).decode("utf-8").split("\0")
    tracked = [name for name in tracked if name]
    missing = [name for name in REQUIRED_TRACKED if name not in tracked or not (root / name).is_file()]
    if missing:
        raise BuildError("required release closure is missing tracked files: " + ", ".join(missing))
    stage = str(_git(root, "ls-files", "--stage"))
    submodules = [line for line in stage.splitlines() if line.startswith("160000 ")]
    if submodules:
        raise BuildError("submodule entries are unsupported in preview archive: " + "; ".join(submodules))
    return {
        "head": head,
        "short": short,
        "commit_time": commit_time,
        "tracked_file_count": len(tracked),
        "tracked_files": tracked,
    }


def run_static_preflight(root: Path) -> dict:
    cmd = [sys.executable, str(root / "release/first_run_smoke_v1/preflight.py"), "--root", str(root)]
    completed = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise BuildError(f"preflight produced non-JSON output (rc={completed.returncode}): {completed.stdout!r} {completed.stderr!r}") from error
    if completed.returncode != 0 or report.get("passed") is not True:
        raise BuildError("static preflight failed: " + json.dumps(report, ensure_ascii=False))
    return report


def deterministic_archive(root: Path, prefix: str) -> bytes:
    tar_bytes = bytes(_git(root, "archive", "--format=tar", f"--prefix={prefix}/", "HEAD", binary=True))
    # Git archive is deterministic for a fixed commit. Normalize only the gzip header.
    import io
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, compresslevel=9, mtime=0) as gz:
        gz.write(tar_bytes)
    return buffer.getvalue()


def verify_archive_bytes(archive: bytes, prefix: str) -> dict:
    import io
    required_names = {f"{prefix}/{name}" for name in REQUIRED_TRACKED}
    with gzip.GzipFile(fileobj=io.BytesIO(archive), mode="rb") as gz:
        tar_bytes = gz.read()
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tf:
        names = set(tf.getnames())
        missing = sorted(required_names - names)
        if missing:
            raise BuildError("archive omitted required tracked files: " + ", ".join(missing))
        launcher = tf.getmember(f"{prefix}/runtime/golden-demo-v3.sh")
        setup = tf.getmember(f"{prefix}/runtime/setup-golden-demo-v3.sh")
        if launcher.mode & 0o111 == 0 or setup.mode & 0o111 == 0:
            raise BuildError("archive did not preserve executable launcher modes")
    return {"member_count": len(names), "required_files_present": True, "launcher_modes_preserved": True}


def extracted_preflight(archive: bytes, prefix: str) -> dict:
    import io
    with tempfile.TemporaryDirectory(prefix="agent-interface-preview-verify-") as td:
        base = Path(td)
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tf:
            tf.extractall(base, filter="data")
        extracted = base / prefix
        return run_static_preflight(extracted)


def build(root: Path, out: Path) -> dict:
    root = root.resolve()
    meta = inspect_rc(root)
    checkout_preflight = run_static_preflight(root)
    version = f"research-preview-{RELEASE_DATE}+{meta['short']}"
    prefix = f"agent-interface-{version}"
    archive = deterministic_archive(root, prefix)
    archive_check = verify_archive_bytes(archive, prefix)
    archive_preflight = extracted_preflight(archive, prefix)
    digest = _sha256(archive)
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    archive_name = prefix + ".tar.gz"
    archive_path = out / archive_name
    if archive_path.exists():
        raise BuildError(f"refusing to overwrite existing artifact: {archive_path}")
    archive_path.write_bytes(archive)
    manifest = {
        "schema": "agent_interface_research_preview_manifest_v1",
        "channel": CHANNEL,
        "version": version,
        "release_date": RELEASE_DATE,
        "revision": meta["head"],
        "commit_time": meta["commit_time"],
        "support": {
            "tested_runtime_target": "WSLg / Linux-X11 with Windows Codex CLI bridge",
            "native_windows": "not claimed in RC1",
            "native_macos": "not claimed in RC1",
            "generic_linux": "not claimed beyond documented prerequisites",
        },
        "artifact": {"name": archive_name, "bytes": len(archive), "sha256": digest},
        "tracked_file_count": meta["tracked_file_count"],
        "required_closure": list(REQUIRED_TRACKED),
        "checks": {
            "checkout_static_preflight": checkout_preflight.get("status"),
            "archive_static_preflight": archive_preflight.get("status"),
            **archive_check,
        },
        "limitations": [
            "Packaging/static checks do not replace supported-host setup/doctor.",
            "A fresh model-backed golden run and audit-live are separate release acceptance gates.",
            "This is a Research Preview, not a stable cross-platform release.",
        ],
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    (out / "SHA256SUMS").write_text(f"{digest}  {archive_name}\n", encoding="utf-8", newline="\n")
    (out / "VERSION").write_text(version + "\n", encoding="utf-8", newline="\n")
    shutil.copyfile(root / "release/preview_bundle_v1/QUICKSTART.md", out / "QUICKSTART.md")
    shutil.copyfile(root / "release/preview_bundle_v1/SUPPORT.md", out / "SUPPORT.md")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, default=Path("artifacts-local/research-preview"))
    args = parser.parse_args()
    try:
        manifest = build(args.root, args.out)
    except BuildError as error:
        parser.exit(2, f"BUILD_FAIL: {error}\n")
    print(json.dumps(manifest, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
