"""Build the portable unified Agent Interface runtime zipapp deterministically."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

FIXED_TIME = (1980, 1, 1, 0, 0, 0)
SCHEMA = "agent-interface/portable-runtime-build-v1"

SOURCE_FILES = (
    "runtime/core_v1/__init__.py",
    "runtime/core_v1/backend.py",
    "runtime/core_v1/contract.py",
    "runtime/core_v1/sequence.py",
    "runtime/core_v1/doctor.py",
    "runtime/core_v1/platform_probe.py",
    "runtime/selector_v1/__init__.py",
    "runtime/selector_v1/selector.py",
    "runtime/cli_v1/__init__.py",
    "runtime/cli_v1/__main__.py",
    "runtime/cli_v1/api.py",
    "runtime/cli_v1/receipt.py",
    "runtime/cli_v1/review.py",
    "runtime/cli_v1/receipt_references.py",
    "runtime/cli_v1/receipt_image.py",
    "runtime/cli_v1/observe.py",
    "runtime/cli_v1/golden_v3.py",
    "runtime/motor_state_v1/__init__.py",
    "runtime/motor_state_v1/adapter.py",
    "runtime/backends/x11_v1/__init__.py",
    "runtime/backends/x11_v1/backend.py",
    "runtime/backends/x11_v1/capture_artifacts.py",
    "runtime/backends/x11_v1/session.py",
    "runtime/backends/win32_v1/__init__.py",
    "runtime/backends/win32_v1/backend.py",
    "runtime/backends/win32_v1/session.py",
    "runtime/backends/quartz_v1/__init__.py",
    "runtime/backends/quartz_v1/backend.py",
    "runtime/backends/quartz_v1/session.py",
)

GENERATED = {
    "runtime/__init__.py": b"\n",
    "runtime/backends/__init__.py": b"\n",
    "__main__.py": b"from runtime.cli_v1.__main__ import main\nraise SystemExit(main())\n",
}

SUPPORT = {
    "schema": "agent-interface/portable-runtime-support-v1",
    "python_minimum": "3.12",
    "promoted_backends": {
        "linux_x11": {"backend_id": "x11-v1", "extra_dependency": "python-xlib", "target_kind": "x11_window_id"},
        "windows": {"backend_id": "win32-v1", "extra_dependency": None, "target_kind": "hwnd"},
        "macos": {"backend_id": "quartz-v1", "extra_dependency": None, "target_kind": "pid", "permissions": ["Accessibility", "Screen Recording"]},
    },
    "wayland": {"promoted": False, "reason": "WAYLAND_BACKEND_NOT_PROMOTED"},
    "automatic_target_discovery": False,
    "automatic_permission_escalation": False,
    "optional_dependencies": {"x11_png_artifacts": ["Pillow"]},
}


def _source_revision(root: Path) -> str | None:
    if not (root / ".git").exists():
        return None
    try:
        value = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD^{commit}"],
            stderr=subprocess.STDOUT).decode('ascii').strip()
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', value):
            raise ValueError('full commit object ID required')
        return value
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        raise RuntimeError('cannot pin committed build source') from error


def _source_bytes(root: Path, rel: str, revision: str | None) -> bytes:
    if revision is not None:
        try:
            return subprocess.check_output(["git", "-C", str(root), "show", f"{revision}:{rel}"], stderr=subprocess.STDOUT)
        except (OSError, subprocess.CalledProcessError) as error:
            detail = getattr(error, "output", b"")
            if isinstance(detail, bytes):
                detail = detail.decode("utf-8", "replace")
            raise RuntimeError(f"cannot read committed source {rel}: {detail}") from error
    return (root / rel).read_bytes()


def _info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.flag_bits = 0
    return info


def build(root: Path, out: Path, manifest_out: Path, sums_out: Path) -> dict:
    revision = _source_revision(root)
    entries: dict[str, bytes] = dict(GENERATED)
    source_manifest = []
    for rel in SOURCE_FILES:
        data = _source_bytes(root, rel, revision)
        entries[rel] = data
        source_manifest.append({"path": rel, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    support_bytes = (json.dumps(SUPPORT, indent=2, sort_keys=True) + "\n").encode()
    entries["SUPPORT.json"] = support_bytes
    build_meta = {
        "schema": SCHEMA,
        "source_revision": revision,
        "source_files": source_manifest,
        "generated_entries": sorted(GENERATED),
        "support_sha256": hashlib.sha256(support_bytes).hexdigest(),
        "research_tree_included": False,
        "tests_included": False,
        "fixtures_included": False,
    }
    entries["BUILD.json"] = (json.dumps(build_meta, sort_keys=True, separators=(",", ":")) + "\n").encode()

    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True) as archive:
        for name in sorted(entries):
            archive.writestr(_info(name), entries[name])

    raw = out.read_bytes()
    result = {
        "schema": "agent-interface/portable-runtime-manifest-v1",
        "source_revision": revision,
        "artifact": out.name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "entries": sorted(entries),
        "source_files": source_manifest,
        "support": SUPPORT,
    }
    manifest_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sums_out.write_text(f"{result['sha256']}  {out.name}\n", encoding="utf-8")
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--sums", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(build(a.root.resolve(), a.out, a.manifest, a.sums), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
