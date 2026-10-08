#!/usr/bin/env python3
"""Construction-only tests. No formal candidate/auditor invocation."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public.json"
TRUTH = ROOT / "truth.json"


def run(script):
    raw = subprocess.run([sys.executable, str(ROOT / script), str(PUBLIC)], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return json.loads(raw.stdout)


def main():
    candidate, audit = run("candidate.py"), run("audit.py")
    expected = json.loads(TRUTH.read_text(encoding="utf-8"))["expected"]
    assert candidate["cases"] == expected, ("candidate fixture mismatch", candidate["cases"])
    assert audit["cases"] == expected, ("independent oracle mismatch", audit["cases"])
    assert candidate["cases"] == audit["cases"]
    print(f"construction PASS: candidate and independently structured auditor match {len(expected)} authored dispositions")


if __name__ == "__main__":
    main()
