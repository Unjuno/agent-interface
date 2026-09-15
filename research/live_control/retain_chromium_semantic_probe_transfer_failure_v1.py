"""Retain the first Chromium transfer outcome without rerunning it."""
import hashlib
import json
import os
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE/"results/chromium-semantic-probe-transfer-live-01"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    report = json.loads((ROOT/"report.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT/"audit.json").read_text(encoding="utf-8"))
    files = sorted(path for path in ROOT.rglob("*") if path.is_file()
                   and path.name not in ("retention.json", "retained-audit.json"))
    manifest = {path.relative_to(ROOT).as_posix(): sha(path) for path in files}
    receipt = {
        "schema": "chromium-semantic-probe-transfer-retention-v1",
        "decision": "RETAIN_FIRST_OUTCOME_NO_RETRY",
        "formal_passed": report["passed"],
        "audit_passed": audit["passed"],
        "failure_class": "generated_reconciliation_count_exceeds_client_consumption",
        "diagnosis": ("The client correctly stopped at the first useful probe. The frozen "
            "gate incorrectly required all later backend reconciliations to equal the number "
            "of probes the client consumed; 4 were generated and 3 were consumed. Every "
            "consumed probe independently rescored and reconciled exactly."),
        "repair_boundary": ("In a new allocation, require every generated reconciliation to "
            "match its exact artifact and require each consumed probe to have one matching "
            "reconciliation. Do not require equal collection cardinality."),
        "manifest": manifest, "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "retry_count": 0,
    }
    temporary = ROOT/"retention.json.tmp"
    temporary.write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    os.replace(temporary, ROOT/"retention.json")
    print(json.dumps({key: receipt[key] for key in
        ("decision", "formal_passed", "audit_passed", "failure_class", "files", "bytes")},
        indent=2))


if __name__ == "__main__": main()
