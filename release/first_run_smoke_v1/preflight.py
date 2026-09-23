"""Read-only launcher/package boundary check; never runs setup, GUI, or a model."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

SCRIPTS = ("runtime/setup-golden-demo-v3.sh", "runtime/golden-demo-v3.sh")
FILES = (*SCRIPTS, "runtime/golden_desktop_demo_v3.py", "runtime/requirements-golden.txt")
LIMITATION = "Launcher boundary only: not dependency installation, doctor, GUI, model, or full source-closure validation."


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def inspect(root: Path) -> dict:
    """Check Git's committed mode as well as the actual checkout when available."""
    root = root.resolve()
    checks = []
    def record(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(ok), "detail": detail})
    tracked = {}
    revision = None
    git_mode = (root / ".git").exists()
    if git_mode:
        try:
            top = subprocess.check_output(["git", "-C", str(root), "rev-parse", "--show-toplevel"], timeout=5).decode().strip()
            if Path(top).resolve() != root:
                raise ValueError("--root must be the repository root")
            revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "--verify", "HEAD"], timeout=5).decode().strip()
            raw = subprocess.check_output(["git", "-C", str(root), "ls-tree", "-z", revision, "--", *FILES], timeout=5)
            for entry in raw.split(b"\0"):
                if entry:
                    meta, name = entry.split(b"\t", 1)
                    mode, kind, sha = meta.decode("ascii").split()
                    tracked[name.decode("utf-8")] = (mode, kind, sha)
            record("committed_tree", True, revision)
        except (OSError, subprocess.SubprocessError, ValueError, UnicodeError) as error:
            record("committed_tree", False, str(error))
    else:
        record("archive_mode", True, "No .git: only extracted files are checked; no committed-mode claim.")
    record("posix_execution", os.name == "posix", "Native Windows execution is outside this check.")
    record("bash_available", shutil.which("bash") is not None, "Required by the existing launchers.")
    for name in FILES:
        path = root / name
        if any(part.is_symlink() for part in (path, *path.parents[:len(Path(name).parts)-1])):
            record(name + ":regular_file", False, "Symlink in required path.")
            continue
        try:
            if not path.is_file():
                raise ValueError("Required regular file is missing.")
            data = path.read_bytes()
            text = data.decode("utf-8")
            record(name + ":readable", True, "sha256:" + hashlib.sha256(data).hexdigest())
        except (OSError, ValueError, UnicodeError) as error:
            record(name + ":readable", False, str(error))
            continue
        if git_mode:
            meta = tracked.get(name)
            record(name + ":committed_bytes", meta is not None and meta[1] == "blob" and meta[2] == git_blob(data), "Worktree bytes must match the frozen HEAD; uncommitted changes are not release evidence.")
            if name in SCRIPTS:
                record(name + ":committed_executable", meta is not None and meta[0] == "100755", "Expected committed Git mode 100755; local chmod alone is insufficient.")
        if name in SCRIPTS:
            record(name + ":filesystem_executable", os.name == "posix" and bool(path.stat().st_mode & 0o111) and os.access(path, os.X_OK), "Direct ./ invocation must be executable in this checkout.")
            record(name + ":bash_lf", data.startswith(b"#!/usr/bin/env bash\n") and b"\r" not in data, "Expected LF bash shebang and no CR bytes.")
        elif name.endswith(".py"):
            try:
                ast.parse(text, filename=name)
                record(name + ":syntax", True, "Parsed only, never imported.")
            except SyntaxError as error:
                record(name + ":syntax", False, str(error))
        else:
            pins = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
            names = [line.split("==")[0].lower().replace("_", "-").replace(".", "-") for line in pins]
            valid = bool(pins) and all(re.fullmatch(r"[A-Za-z0-9_.-]+==[A-Za-z0-9_.+!-]+", line) for line in pins) and len(names) == len(set(names))
            record(name + ":exact_pins", valid, "Nonempty, unique exact version pins; wheel availability and transitive closure are not checked.")
    passed = all(item["passed"] for item in checks)
    return {"schema": "agent_interface_first_run_preflight_v1", "status": "PASS_LAUNCHER_BOUNDARY" if passed else "FAIL_LAUNCHER_BOUNDARY", "passed": passed, "root": str(root), "revision": revision, "mode_source": "committed_git_and_filesystem" if git_mode else "archive_filesystem_only", "checks": checks, "limitations": [LIMITATION]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, help="Optional new JSON file; refuses to overwrite.")
    args = parser.parse_args()
    report = inspect(args.root)
    encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        try:
            with args.out.open("x", encoding="utf-8") as stream:
                stream.write(encoded)
        except OSError as error:
            parser.exit(2, f"Cannot retain new report: {error}\n")
    print(encoded, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
