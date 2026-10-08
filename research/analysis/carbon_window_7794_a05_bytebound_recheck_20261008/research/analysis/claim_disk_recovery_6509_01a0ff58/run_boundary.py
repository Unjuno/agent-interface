"""Nine prospective process-exit boundaries. Exclusive outputs; no retries."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SOURCE_NAMES = ("recovery.py", "child.py", "cases.json", "run_boundary.py", "audit.py", "test_recovery.py")
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main(destination):
    out = Path(destination).resolve()
    out.mkdir(exist_ok=False)
    cases = json.loads((HERE / "cases.json").read_text())
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    actual = {name: sha(HERE / name) for name in SOURCE_NAMES}
    if freeze["sources"] != actual:
        raise RuntimeError("source freeze mismatch")
    rows = []
    started = datetime.now(timezone.utc).isoformat()
    for case in cases:
        target = out / case["id"]
        records = []
        for mode in ("write", "read", "read"):
            args = [sys.executable, str(HERE / "child.py"), mode, str(target), json.dumps(case, sort_keys=True)]
            begin = datetime.now(timezone.utc).isoformat()
            process = subprocess.run(args, capture_output=True, timeout=15)
            records.append(dict(mode=mode, argv=[Path(sys.executable).name, "child.py", mode, case["id"], json.dumps(case, sort_keys=True)],
                started_utc=begin, ended_utc=datetime.now(timezone.utc).isoformat(),
                exit_code=process.returncode, stdout=process.stdout.decode(), stderr=process.stderr.decode()))
            expected = 73 if mode == "write" else 0
            if process.returncode != expected:
                failure = dict(case=case, processes=records, status="STOP_UNEXPECTED_PROCESS_EXIT")
                (out / (case["id"] + "-STOP.json")).write_text(json.dumps(failure, indent=2))
                raise RuntimeError("unexpected " + mode + " exit; no retry")
        before = (target / "receipts.jsonl").read_bytes()
        cached = target / "cached-verdict.json"
        row = dict(case=case, processes=records,
            recovery=json.loads(records[1]["stdout"]), second_recovery=json.loads(records[2]["stdout"]),
            journal_sha256=hashlib.sha256(before).hexdigest(),
            always_unknown="PARTIAL_UNKNOWN",
            trust_cached=json.loads(cached.read_text())["disposition"] if cached.exists() else "PARTIAL_UNKNOWN")
        rows.append(row)
        print(case["id"], row["recovery"]["disposition"], flush=True)
    raw = dict(schema="disk-prefix-process-boundary-v1", sources=actual,
        started_utc=started, ended_utc=datetime.now(timezone.utc).isoformat(),
        environment=dict(python=sys.version, platform=platform.platform(), executable_sha256=sha(Path(sys.executable))),
        rows=rows)
    with (out / "raw.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(raw, stream, indent=2)
        stream.write("\n")

if __name__ == "__main__":
    main(sys.argv[1])
