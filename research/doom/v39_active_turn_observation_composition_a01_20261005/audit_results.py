"""Read-only audit for the preserved A01 construction test transcript."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "planner-adapter": 12,
    "app-server-client": 4,
    "v39-paired-signal": 21,
    "v39-controller": 5,
    "v39-wait": 10,
    "v39-pair-dispatch": 1,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def read_console_log(path: Path) -> str:
    """Decode native PowerShell redirection (UTF-16LE) or UTF-8 test logs."""
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def verify_hashes() -> None:
    manifest = ROOT / "SHA256SUMS"
    require(manifest.is_file(), "SHA256SUMS is missing")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = ROOT / relative
        require(path.is_file(), f"manifest file is missing: {relative}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        require(actual == expected, f"SHA-256 mismatch: {relative}")


def audit() -> dict:
    verify_hashes()
    total = 0
    counts = {}
    for name, expected_count in EXPECTED.items():
        log = ROOT / "results" / f"{name}.txt"
        exit_path = ROOT / "results" / f"{name}.txt.exit"
        require(exit_path.read_text(encoding="ascii").strip() == "0",
                f"{name}: nonzero process exit")
        content = read_console_log(log)
        match = re.search(r"Ran (\d+) tests? in ", content)
        require(match is not None, f"{name}: unittest count missing")
        count = int(match.group(1))
        require(count == expected_count, f"{name}: expected {expected_count}, saw {count}")
        require("OK" in content.splitlines()[-1],
                f"{name}: unittest did not report OK")
        counts[name] = count
        total += count
    compile_exit = (ROOT / "results" / "py-compile.txt.exit").read_text(encoding="ascii").strip()
    require(compile_exit == "0", "py_compile exited nonzero")
    return {"status": "PASS_RETAINED_CONSTRUCTION_TRANSCRIPT",
            "test_counts": counts, "total_tests": total,
            "py_compile": "PASS",
            "scope": "Test process evidence only; no model inference or live control."}


if __name__ == "__main__":
    import json
    print(json.dumps(audit(), indent=2))
