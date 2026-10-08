"""Retain the repaired Chromium transfer outcome without rerunning it."""
import hashlib
import json
import os
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE/"results/chromium-semantic-probe-transfer-live-02"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    report = json.loads((ROOT/"report.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT/"audit.json").read_text(encoding="utf-8"))
    files = sorted(path for path in ROOT.rglob("*") if path.is_file()
                   and path.name not in ("retention.json", "retained-audit.json"))
    receipt = {
        "schema": "chromium-semantic-probe-transfer-retention-v2",
        "decision": "RETAIN_FIRST_OUTCOME_NO_RETRY",
        "formal_passed": report["passed"], "audit_passed": audit["passed"],
        "claim": ("One deterministic Chromium completion predicate transferred the "
            "no-authority pre-artifact semantic feedback contract with exact negative "
            "rejection, positive detection, durable reconciliation, independent output, "
            "and empty release."),
        "limits": ("One scripted Linux/X11 fixture and one fresh seed. No rate, model, "
            "token, general GUI, causal speed, portability, or human-tempo claim."),
        "manifest": {path.relative_to(ROOT).as_posix(): sha(path) for path in files},
        "files": len(files), "bytes": sum(path.stat().st_size for path in files),
        "retry_count": 0,
    }
    temporary = ROOT/"retention.json.tmp"
    temporary.write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    os.replace(temporary, ROOT/"retention.json")
    print(json.dumps({key: receipt[key] for key in
        ("decision", "formal_passed", "audit_passed", "files", "bytes")}, indent=2))


if __name__ == "__main__": main()
