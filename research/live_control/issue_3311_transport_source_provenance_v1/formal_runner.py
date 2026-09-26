"""Run one read-only source-provenance re-audit over all retained runs."""
import json
from pathlib import Path
import audit_v2
root=Path(__file__).resolve().parent
reports=[]
for run in sorted(audit_v2.MANIFEST):
    reports.append(audit_v2.audit(root/"evidence"/run))
print(json.dumps(reports,indent=2))
