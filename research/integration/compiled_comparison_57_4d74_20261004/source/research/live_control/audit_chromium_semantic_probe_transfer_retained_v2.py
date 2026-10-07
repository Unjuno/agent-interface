"""Audit the retained repaired Chromium transfer."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE/"results/chromium-semantic-probe-transfer-live-02"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    receipt = read(ROOT/"retention.json"); report = read(ROOT/"report.json")
    checks = {
        "manifest": all((ROOT/name).is_file() and sha(ROOT/name) == digest
                        for name, digest in receipt["manifest"].items()),
        "first_pass": receipt["formal_passed"] is True and
                      receipt["audit_passed"] is True and report["passed"] is True,
        "all_formal_checks": all(report["checks"].values()),
        "negative_positive_independent": (
            report["checks"]["blank_rejected"] is True and
            report["checks"]["submission_detected"] is True and
            report["checks"]["independent_saved_value"] is True),
        "pre_artifact": report["metrics_ms"]["useful_probe_to_image_ready_ms"] > 0,
        "early_terminal": report["metrics_ms"]["useful_client_to_terminal_ms"] > 0,
        "no_authority_release": (report["checks"]["all_probes_no_authority"] is True and
                                 report["checks"]["terminal_empty_release"] is True),
        "no_retry_model": receipt["retry_count"] == report["retry_count"] == 0 and
                          report["model_calls"] == 0,
    }
    result = {"passed": all(checks.values()), "checks": checks,
              "metrics_ms": report["metrics_ms"], "files": receipt["files"],
              "bytes": receipt["bytes"], "limits": receipt["limits"]}
    (ROOT/"retained-audit.json").write_text(json.dumps(result, indent=2)+"\n",
                                             encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
