"""Prove the independent audit rejects mutations of candidate/raw evidence."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

RAW, OUT = Path(sys.argv[1]), Path(sys.argv[2])
if RAW.resolve() == OUT.resolve() or RAW.resolve() in OUT.resolve().parents:
    raise SystemExit("corruption-control output must be outside immutable raw input")
OUT.mkdir(parents=True, exist_ok=True)


def run_control(name, mutate):
    base = OUT / name
    inp, report = base / "input", base / "report"
    shutil.copytree(RAW, inp)
    report.mkdir(parents=True)
    mutate(inp)
    proc = subprocess.run([sys.executable, "-B", "research/integration/issue_2918_xcalc_v1/audit_allocation.py",
                           str(inp), str(report)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    rejected = proc.returncode != 0 and "AssertionError" in proc.stderr
    return {"control": name, "auditor_exit_code": proc.returncode,
            "rejected_by_assertion": rejected,
            "stderr_tail": proc.stderr.strip().splitlines()[-1:]}


def wrong_candidate_decision(inp):
    p = inp / "candidate_results.json"
    rows = json.loads(p.read_text())
    next(r for r in rows if r["case"] == "effect_unmasked_10")["disposition"] = "FORWARD"
    p.write_text(json.dumps(rows, sort_keys=True, indent=2) + "\n")


def missing_row(inp):
    for fname in ("candidate_results.json", "sealed_oracle.json"):
        p = inp / fname
        rows = json.loads(p.read_text())
        rows.pop(0)
        p.write_text(json.dumps(rows, sort_keys=True, indent=2) + "\n")


def changed_png(inp):
    rows = json.loads((inp / "candidate_results.json").read_text())
    row = next(r for r in rows if r["case"] == "effect_unmasked_10")
    p = inp / "captures" / Path(row["artifact_path"]).name
    im = Image.open(p).convert("RGB")
    old = im.getpixel((198, 5))
    im.putpixel((198, 5), (255, 0, 255) if old != (255, 0, 255) else (0, 255, 255))
    im.save(p, format="PNG")


def main():
    results = [run_control("wrong_disposition", wrong_candidate_decision),
               run_control("missing_row", missing_row),
               run_control("mutated_capture_pixel", changed_png)]
    assert all(r["rejected_by_assertion"] for r in results), results
    result = {"decision": "PASS_AUDIT_CORRUPTION_CONTROLS",
              "source_raw_unchanged": True, "controls": results}
    (OUT / "corruption_controls.json").write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
