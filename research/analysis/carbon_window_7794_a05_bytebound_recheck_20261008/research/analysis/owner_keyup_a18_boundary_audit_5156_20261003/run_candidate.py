import hashlib
import json
import os
import sys
from pathlib import Path
from boundary_audit import audit, legacy
from mutations import cases

HERE = Path(__file__).resolve().parent


def main():
    out = Path(sys.argv[1])
    out.mkdir(exist_ok=False)
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for name, digest in freeze["files"].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
    raw = json.loads((HERE / "retained/raw.json").read_text())
    rows = []
    for name, item, invalid in cases(raw):
        path = out / (name + ".json")
        path.write_text(json.dumps(item, sort_keys=True, indent=2) + "\n")
        rows.append({"case": name, "invalid": invalid,
                     "legacy_errors": legacy.audit(item), "supplemental_errors": audit(item),
                     "raw_file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    report = {"run_id": freeze["run_id"], "pid": os.getpid(), "python": sys.version,
              "rows": rows, "legacy_false_accepts": sum(r["invalid"] and not r["legacy_errors"] for r in rows),
              "supplemental_matches": sum(bool(r["supplemental_errors"]) == r["invalid"] for r in rows),
              "scope": "retained-raw mutation construction only; no X11, input, model or game"}
    (out / "candidate.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, sort_keys=True))
    return 0 if report["supplemental_matches"] == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
