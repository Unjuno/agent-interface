"""Write immutable allocation closeout metadata after the candidate/audit containers exit."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).is_file() else None


def main(results_dir, audit_exit, audit_container_id):
    out = Path(results_dir).resolve()
    candidate = json.loads((out / "candidate-host-receipt.json").read_text(encoding="utf-8"))
    if (out / "RUN.json").is_file():
        report = json.loads((out / "RUN.json").read_text(encoding="utf-8"))
    else:
        report = {"allocation": "5156-RUNNER-COMPLETE-SENTINEL-T0-ORB-20261001-03",
                  "scientific_disposition": "STOP_CANDIDATE_DID_NOT_WRITE_RUN_RECEIPT"}
    receipt = {
        "schema": "runner-completion-sentinel-allocation-closeout-v1",
        "allocation": report["allocation"],
        "candidate_container_id": candidate["container_id"],
        "candidate_exit_code": candidate["candidate_exit_code"],
        "auditor_invocations": 1 if candidate["candidate_exit_code"] == 0 else 0,
        "auditor_container_id": audit_container_id if candidate["candidate_exit_code"] == 0 else None,
        "auditor_exit_code": int(audit_exit) if candidate["candidate_exit_code"] == 0 else None,
        "candidate_receipt_sha256": sha256(out / "candidate-host-receipt.json"),
        "run_receipt_sha256": sha256(out / "RUN.json"),
        "independent_audit_stdout_sha256": sha256(out / "independent-audit.stdout.txt"),
        "independent_audit_stderr_sha256": sha256(out / "independent-audit.stderr.txt"),
        "closed_at_utc": datetime.now(timezone.utc).isoformat(),
        "retry": False,
        "interpretation": report["scientific_disposition"],
    }
    (out / "ALLOCATION_CLOSEOUT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                                                   encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: record_allocation_closeout.py RESULTS AUDIT_EXIT AUDITOR_CID")
    raise SystemExit(main(*sys.argv[1:]))
