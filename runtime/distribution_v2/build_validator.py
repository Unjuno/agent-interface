"""Build a standalone static-validator zipapp, without native dispatch code.

Run: python -m runtime.distribution_v2.build_validator --out validator.pyz
The existing validator becomes __main__.py verbatim. A Git checkout is read
from HEAD, not the working tree. An exported source directory is labelled as
an unpinned directory snapshot. Building does not validate or execute programs.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

SOURCE_MAP = (
    ("runtime/cli_v1/validate_program.py", "__main__.py"),
    ("runtime/core_v1/__init__.py", "runtime/core_v1/__init__.py"),
    ("runtime/core_v1/contract.py", "runtime/core_v1/contract.py"),
    ("runtime/core_v1/sequence.py", "runtime/core_v1/sequence.py"),
    ("runtime/core_v1/platform_probe.py", "runtime/core_v1/platform_probe.py"),
)
SCHEMA = "agent-interface/standalone-validator-build-v1"


def _git(root: Path, *args: str) -> bytes:
    try:
        return subprocess.check_output(["git", "-C", str(root), *args],
                                       stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("cannot read committed validator source") from error


def build(root: Path, out: Path, manifest_out: Path, sums_out: Path) -> dict:
    """Write three new files; refuse existing destinations and source overwrite.

    Standard-library-only sources are copied in full. Source hashes are byte
    identity checks, not source authentication or permission to execute input.
    The trusted output directory must not be concurrently modified.
    """
    root = root.resolve()
    destinations = [p.resolve() for p in (out, manifest_out, sums_out)]
    if len(set(destinations)) != 3:
        raise ValueError("artifact, manifest and checksum paths must differ")
    if any(p.exists() for p in destinations):
        raise FileExistsError("output already exists")
    if set(destinations) & {(root / src).resolve() for src, _ in SOURCE_MAP}:
        raise ValueError("output overlaps source")
    revision = None
    if (root / ".git").exists():
        revision = _git(root, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
            raise RuntimeError("full source commit ID required")
    entries = {"runtime/__init__.py": b"\n"}
    sources = []
    for src, dest in SOURCE_MAP:
        data = (_git(root, "show", f"{revision}:{src}") if revision else
                (root / src).read_bytes())
        entries[dest] = data
        sources.append({"source": src, "entry": dest, "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest()})
    metadata = {
        "schema": SCHEMA, "source_revision": revision,
        "source_kind": "committed" if revision else "directory_snapshot",
        "source_files": sources, "generated_entries": ["runtime/__init__.py"],
        "python_minimum": "3.12", "third_party_dependencies": [],
        "purpose": "static validation only", "runtime_admission": "not_evaluated",
        "backend_included": False, "task_success": None,
    }
    entries["BUILD.json"] = (json.dumps(metadata, sort_keys=True, separators=(",", ":")) + "\n").encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, entries[name])
    raw = buffer.getvalue()
    result = {**metadata, "artifact": out.name, "entries": sorted(entries),
              "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    payloads = (raw, (json.dumps(result, indent=2, sort_keys=True) + "\n").encode(),
                f"{result['sha256']}  {out.name}\n".encode())
    for path, payload in zip(destinations, payloads):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(payload)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = build(args.root, args.out, args.out.with_suffix(".manifest.json"),
                   args.out.with_suffix(".sha256"))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
