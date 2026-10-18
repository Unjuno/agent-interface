import hashlib
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "out"
OUT.mkdir(exist_ok=False)
for directory in (OUT / "db", OUT / "observations", OUT / "process"):
    directory.mkdir(exist_ok=False)
cases = json.loads((ROOT / "cases.json").read_text())
receipts = []
observations = []
for case in cases["cases"]:
    db_path = OUT / "db" / f"{case['id']}.sqlite"
    for stage, command in (
        ("writer", [sys.executable, str(ROOT / "writer.py"), str(db_path), case["writer_mode"]]),
        ("observer", [sys.executable, str(ROOT / "observer.py"), str(db_path), case["id"]]),
    ):
        started = time.time_ns()
        p = subprocess.run(command, text=True, capture_output=True)
        ended = time.time_ns()
        receipt = {"case_id": case["id"], "stage": stage, "command": command, "exit": p.returncode,
                   "stdout": p.stdout, "stderr": p.stderr, "started_unix_ns": started, "ended_unix_ns": ended}
        (OUT / "process" / f"{case['id']}-{stage}.json").write_text(json.dumps(receipt, indent=2) + "\n")
        receipts.append(receipt)
        if p.returncode != 0:
            raise SystemExit(f"STOP_{stage.upper()}_EXIT:{case['id']}:{p.returncode}")
        if stage == "observer":
            observations.append(json.loads(p.stdout))
    receipts[-2]["database_sha256"] = hashlib.sha256(db_path.read_bytes()).hexdigest()
(OUT / "process_receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
(OUT / "observations.json").write_text(json.dumps({"allocation": cases["allocation"], "observations": observations}, indent=2) + "\n")
print(json.dumps({"allocation": cases["allocation"], "cases": len(observations), "processes": len(receipts), "exit": 0}, sort_keys=True))
