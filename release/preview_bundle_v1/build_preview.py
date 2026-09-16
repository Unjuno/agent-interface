"""Build a deterministic Agent Interface Research Preview archive from a clean Git RC.

The preview is not the whole research repository.  It packages an explicit runtime
source closure plus the retained evidence required by ``audit-retained``.  The
extracted archive is then audited again in CI, so an omitted runtime dependency is
a packaging failure rather than an inferred success.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

CHANNEL = "Research Preview"
RELEASE_DATE = "2026-09-17"
RETAINED_DIR = "research/live_control/results/integrated-efficiency-live-01"
RETAINED_FILES = (
    f"{RETAINED_DIR}/preregistration.json",
    f"{RETAINED_DIR}/report.json",
    f"{RETAINED_DIR}/audit.json",
)
ROOT_RELEASE_FILES = ("LICENSE", "README.md", "SECURITY.md")
LIVE_CONTROL_ASSETS = (
    "research/live_control/integrated_efficiency_discoveries_v1.json",
    "research/live_control/plain_form_points_schema_v1.json",
    "research/live_control/plain_form_points_responder_v1.txt",
    "research/live_control/compiled_form_grounding_schema_v1.json",
    "research/live_control/compiled_form_grounding_responder_v1.txt",
)
REQUIRED_TRACKED = (
    "runtime/golden-demo-v3.sh",
    "runtime/setup-golden-demo-v3.sh",
    "runtime/golden_desktop_demo_v3.py",
    "runtime/requirements-golden.txt",
    "release/first_run_smoke_v1/preflight.py",
    "release/preview_bundle_v1/build_preview.py",
    "release/preview_bundle_v1/accept_supported_host.py",
    "release/preview_bundle_v1/QUICKSTART.md",
    "release/preview_bundle_v1/SUPPORT.md",
    "release/preview_bundle_v1/RELEASE_NOTES.md",
    *RETAINED_FILES,
    *LIVE_CONTROL_ASSETS,
)


class BuildError(RuntimeError):
    pass


def _git(root: Path, *args: str, binary: bool = False) -> str | bytes:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), *args], stderr=subprocess.STDOUT
        )
    except (OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, "output", b"")
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", "replace")
        raise BuildError(f"git {' '.join(args)} failed: {detail}") from error
    return out if binary else out.decode("utf-8").strip()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tracked_files(root: Path) -> list[str]:
    raw = bytes(_git(root, "ls-files", "-z", binary=True)).decode("utf-8")
    return sorted(name for name in raw.split("\0") if name)


def retained_source_paths(root: Path) -> set[str]:
    prereg = root / RETAINED_FILES[0]
    if not prereg.is_file():
        raise BuildError(f"missing retained preregistration: {RETAINED_FILES[0]}")
    try:
        value = json.loads(prereg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BuildError("retained preregistration is unreadable") from error
    sources = value.get("sources")
    if type(sources) is not dict or not sources:
        raise BuildError("retained preregistration has no source map")
    result: set[str] = set()
    for name, digest in sources.items():
        if type(name) is not str or not name or "/" in name or "\\" in name:
            raise BuildError(f"unsafe retained source name: {name!r}")
        if type(digest) is not str or len(digest) != 64:
            raise BuildError(f"malformed retained source digest for {name!r}")
        result.add("research/live_control/" + name)
    return result


def select_release_paths(root: Path, tracked: list[str]) -> list[str]:
    tracked_set = set(tracked)
    selected: set[str] = set(ROOT_RELEASE_FILES)
    selected.update(name for name in tracked if name.startswith("runtime/"))
    selected.update(name for name in tracked if name.startswith("release/"))
    selected.update(
        name for name in tracked
        if name.startswith("research/live_control/")
        and "/" not in name.removeprefix("research/live_control/")
        and name.endswith(".py")
    )
    selected.update(LIVE_CONTROL_ASSETS)
    selected.update(RETAINED_FILES)
    selected.update(retained_source_paths(root))
    missing = sorted(name for name in selected if name not in tracked_set or not (root / name).is_file())
    if missing:
        raise BuildError("selected release closure has missing tracked files: " + ", ".join(missing))
    required_missing = sorted(set(REQUIRED_TRACKED) - selected)
    if required_missing:
        raise BuildError("selection policy omitted required paths: " + ", ".join(required_missing))
    return sorted(selected)


def inspect_rc(root: Path) -> dict:
    root = root.resolve()
    if not (root / ".git").exists():
        raise BuildError("build must run from a Git checkout")
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise BuildError("release build requires a clean checkout; dirty paths:\n" + str(status))
    head = str(_git(root, "rev-parse", "--verify", "HEAD"))
    short = str(_git(root, "rev-parse", "--short=12", "HEAD"))
    commit_time = str(_git(root, "show", "-s", "--format=%cI", "HEAD"))
    tracked = tracked_files(root)
    selected = select_release_paths(root, tracked)
    stage = str(_git(root, "ls-files", "--stage", "--", *selected))
    submodules = [line for line in stage.splitlines() if line.startswith("160000 ")]
    if submodules:
        raise BuildError("submodule entries are unsupported in preview closure")
    return {
        "head": head,
        "short": short,
        "commit_time": commit_time,
        "tracked_file_count": len(tracked),
        "selected_file_count": len(selected),
        "selected_files": selected,
    }


def run_static_preflight(root: Path) -> dict:
    cmd = [
        sys.executable,
        str(root / "release/first_run_smoke_v1/preflight.py"),
        "--root", str(root),
    ]
    completed = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise BuildError(
            f"preflight produced non-JSON output (rc={completed.returncode}): "
            f"{completed.stdout!r} {completed.stderr!r}"
        ) from error
    if completed.returncode != 0 or report.get("passed") is not True:
        raise BuildError("static preflight failed: " + json.dumps(report, ensure_ascii=False))
    return report


def deterministic_archive(root: Path, prefix: str, paths: list[str]) -> bytes:
    if not paths:
        raise BuildError("refusing to build an empty release closure")
    tar_bytes = bytes(
        _git(
            root, "archive", "--format=tar", f"--prefix={prefix}/",
            "HEAD", "--", *paths, binary=True
        )
    )
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, compresslevel=9, mtime=0) as gz:
        gz.write(tar_bytes)
    return buffer.getvalue()


def verify_archive_bytes(archive: bytes, prefix: str, selected: list[str]) -> dict:
    required_names = {f"{prefix}/{name}" for name in REQUIRED_TRACKED}
    selected_names = {f"{prefix}/{name}" for name in selected}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tf:
        names = {member.name for member in tf.getmembers() if member.isfile()}
        missing = sorted(required_names - names)
        unexpected = sorted(names - selected_names)
        selected_missing = sorted(selected_names - names)
        if missing:
            raise BuildError("archive omitted required files: " + ", ".join(missing))
        if unexpected:
            raise BuildError("archive contains unselected files: " + ", ".join(unexpected[:20]))
        if selected_missing:
            raise BuildError("archive omitted selected files: " + ", ".join(selected_missing[:20]))
        launcher = tf.getmember(f"{prefix}/runtime/golden-demo-v3.sh")
        setup = tf.getmember(f"{prefix}/runtime/setup-golden-demo-v3.sh")
        if launcher.mode & 0o111 == 0 or setup.mode & 0o111 == 0:
            raise BuildError("archive did not preserve executable launcher modes")
    return {
        "member_count": len(names),
        "required_files_present": True,
        "selected_closure_exact": True,
        "launcher_modes_preserved": True,
    }


def extracted_preflight(archive: bytes, prefix: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="agent-interface-preview-verify-") as td:
        base = Path(td)
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tf:
            tf.extractall(base, filter="data")
        return run_static_preflight(base / prefix)


def build(root: Path, out: Path) -> dict:
    root = root.resolve()
    meta = inspect_rc(root)
    checkout_preflight = run_static_preflight(root)
    version = f"research-preview-{RELEASE_DATE}+{meta['short']}"
    prefix = f"agent-interface-{version}"
    archive = deterministic_archive(root, prefix, meta["selected_files"])
    archive_check = verify_archive_bytes(archive, prefix, meta["selected_files"])
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
        "schema": "agent_interface_research_preview_manifest_v2",
        "channel": CHANNEL,
        "version": version,
        "release_date": RELEASE_DATE,
        "revision": meta["head"],
        "commit_time": meta["commit_time"],
        "support": {
            "preview_target": "WSLg / Linux-X11 with Windows Codex CLI bridge",
            "native_windows": "not claimed in RC1",
            "native_macos": "not claimed in RC1",
            "generic_linux": "not claimed beyond documented prerequisites",
        },
        "artifact": {"name": archive_name, "bytes": len(archive), "sha256": digest},
        "tracked_file_count": meta["tracked_file_count"],
        "selected_file_count": meta["selected_file_count"],
        "selection_policy": [
            "root LICENSE/README/SECURITY",
            "all tracked runtime/**",
            "all tracked release/**",
            "all top-level research/live_control/*.py",
            "explicit Golden Desktop schema/responder assets",
            "retained integrated-efficiency prereg/report/audit",
            "every source named by retained preregistration",
        ],
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
    (out / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (out / "SHA256SUMS").write_text(
        f"{digest}  {archive_name}\n", encoding="utf-8", newline="\n"
    )
    (out / "VERSION").write_text(version + "\n", encoding="utf-8", newline="\n")
    for name in ("QUICKSTART.md", "SUPPORT.md", "RELEASE_NOTES.md"):
        shutil.copyfile(root / "release/preview_bundle_v1" / name, out / name)
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
