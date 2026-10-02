#!/usr/bin/env python3
"""Pre-freeze construction checks for fixture, independent audit, and gates."""
import json
import subprocess
import sys
from pathlib import Path
import candidate

ROOT = Path(__file__).resolve().parent
DESIGN = json.loads((ROOT/"public.json").read_text(encoding="utf-8"))
EXPECTED = json.loads((ROOT/"truth.json").read_text(encoding="utf-8"))["expected"]


def run(script):
    p = subprocess.run([sys.executable,str(ROOT/script),str(ROOT/"public.json")],
                       cwd=ROOT,capture_output=True,text=True,check=True)
    return json.loads(p.stdout)["cases"]


def project(actual, expected):
    return {key:actual[key] for key in expected}


def main():
    cand, audit = run("candidate.py"), run("audit.py")
    assert {k:project(cand[k],v) for k,v in EXPECTED.items()} == EXPECTED
    assert {k:project(audit[k],v) for k,v in EXPECTED.items()} == EXPECTED
    for key in EXPECTED:
        assert project(cand[key],EXPECTED[key]) == project(audit[key],EXPECTED[key])
    sample = DESIGN["cases"][0].copy()
    sample.update(forbidden_effects=1,soft_latency_differences_ms=[-1000]*8)
    assert candidate.evaluate(sample,DESIGN)["binary_claim"] == "HARD_GATE_FAIL"
    sample = DESIGN["cases"][0].copy()
    sample.update(missing=1,margin_preregistered=False)
    assert candidate.evaluate(sample,DESIGN)["binary_claim"] == "HOLD_MISSING_OUTCOMES"
    print(f"construction PASS: candidate/auditor match {len(EXPECTED)} cases; hard-gate and missingness mutations refuse")


if __name__ == "__main__": main()
