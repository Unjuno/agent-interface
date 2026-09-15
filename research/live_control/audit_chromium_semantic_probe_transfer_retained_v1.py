"""Audit the immutable manifest of the failed first Chromium transfer."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE/"results/chromium-semantic-probe-transfer-live-01"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    receipt = read(ROOT/"retention.json"); report = read(ROOT/"report.json")
    checks = {
        "manifest": all((ROOT/name).is_file() and sha(ROOT/name) == digest
                        for name, digest in receipt["manifest"].items()),
        "failure_preserved": receipt["formal_passed"] is False and
            report["passed"] is False and report["checks"]["all_exact_reconciliations"] is False,
        "sole_formal_failure": [name for name, value in report["checks"].items()
                                if not value] == ["all_exact_reconciliations"],
        "functional_evidence": (report["checks"]["blank_rejected"] is True and
            report["checks"]["submission_detected"] is True and
            report["checks"]["independent_saved_value"] is True and
            report["checks"]["pre_artifact_useful"] is True),
        "cardinality_diagnosis": (len(report["reconciliations"]) == 4 and
            sum(len(report["clients"][name]["feedback"])
                for name in ("negative", "positive")) == 3),
        "no_retry": receipt["retry_count"] == report["retry_count"] == 0,
    }
    result = {"passed": all(checks.values()), "checks": checks,
              "files": receipt["files"], "bytes": receipt["bytes"],
              "failure_class": receipt["failure_class"]}
    (ROOT/"retained-audit.json").write_text(json.dumps(result, indent=2)+"\n",
                                             encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
