"""Run one read-only source-provenance re-audit over all retained runs."""
import json
from pathlib import Path
import audit_v2
root=Path(__file__).resolve().parent
def exit_code(reports):
    """Fail closed unless every report has the exact expected PASS disposition."""
    return 0 if reports and all(
        report.get("disposition") == "PASS_V1_SYNTHETIC_TRANSPORT_ONLY"
        and report.get("checks")
        and all(report["checks"].values())
        for report in reports
    ) else 1

def main():
    reports=[]
    for run in sorted(audit_v2.MANIFEST):
        reports.append(audit_v2.audit(root/"evidence"/run))
    print(json.dumps(reports,indent=2))
    return exit_code(reports)

if __name__ == "__main__":
    raise SystemExit(main())
