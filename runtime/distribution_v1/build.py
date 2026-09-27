"""Build a deterministic, dependency-free Agent Interface doctor zipapp."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

SCHEMA = "agent-interface/standalone-doctor-build-v1"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
SOURCE_FILES = (
    "runtime/core_v1/__init__.py",
    "runtime/core_v1/backend.py",
    "runtime/core_v1/contract.py",
    "runtime/core_v1/doctor.py",
    "runtime/core_v1/platform_probe.py",
    "runtime/interface_v1/__init__.py",
    "runtime/interface_v1/__main__.py",
    "runtime/interface_v1/doctor.py",
    "runtime/interface_v1/native_probe.py",
)
GENERATED = {
    "runtime/__init__.py": b"\n",
    "__main__.py": b"from runtime.interface_v1.doctor import main\nraise SystemExit(main())\n",
}


def _info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=FIXED_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.flag_bits = 0
    return info


def _source_bytes(root: Path, rel: str) -> bytes:
    """Use committed bytes in a Git checkout so OS newline conversion is irrelevant."""
    if (root / ".git").exists():
        try:
            return subprocess.check_output(
                ["git", "-C", str(root), "show", f"HEAD:{rel}"],
                stderr=subprocess.STDOUT,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            detail = getattr(error, "output", b"")
            if isinstance(detail, bytes):
                detail = detail.decode("utf-8", "replace")
            raise RuntimeError(f"cannot read committed source {rel}: {detail}") from error
    return (root / rel).read_bytes()


def build(root: Path, out: Path, manifest_out: Path, sums_out: Path) -> dict:
    entries: dict[str, bytes] = dict(GENERATED)
    source_manifest = []
    for rel in SOURCE_FILES:
        data = _source_bytes(root, rel)
        entries[rel] = data
        source_manifest.append({
            "path": rel,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    build_meta = {
        "schema": SCHEMA,
        "source_files": source_manifest,
        "generated_entries": sorted(GENERATED),
        "ready_for_side_effects": False,
        "support_claim": False,
    }
    entries["BUILD.json"] = (json.dumps(build_meta, sort_keys=True, separators=(",", ":")) + "\n").encode()

    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True) as archive:
        for name in sorted(entries):
            archive.writestr(_info(name), entries[name])

    raw = out.read_bytes()
    result = {
        "schema": "agent-interface/standalone-doctor-manifest-v1",
        "artifact": out.name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "entries": sorted(entries),
        "source_files": source_manifest,
        "python_minimum": "3.12",
        "support_claim": False,
        "ready_for_side_effects": False,
    }
    manifest_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sums_out.write_text(f"{result['sha256']}  {out.name}\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--sums", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.root.resolve(), args.out, args.manifest, args.sums), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
