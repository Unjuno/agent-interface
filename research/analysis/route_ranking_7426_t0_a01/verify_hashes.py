#!/usr/bin/env python3
"""Verify the package manifest over canonical UTF-8/LF bytes."""
from __future__ import annotations
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
manifest = ROOT / "SHA256SUMS"
failures = []
checked = 0
for raw in manifest.read_text(encoding="ascii").splitlines():
    expected, name = raw.split("  ", 1)
    data = (ROOT / name).read_bytes()
    canonical = data.replace(b"\r\n", b"\n")
    if b"\r" in canonical:
        failures.append((name, "bare carriage return"))
        continue
    actual = hashlib.sha256(canonical).hexdigest()
    checked += 1
    if actual != expected:
        failures.append((name, actual))
if failures:
    for name, detail in failures:
        print(f"FAIL {name}: {detail}")
    raise SystemExit(1)
print(f"PASS: {checked} canonical-LF SHA-256 entries")
