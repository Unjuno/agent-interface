"""Read-only successor audit: cross-check candidate summaries against receipts."""
import json
import sys
from pathlib import Path

from audit import audit as audit_v1


def audit(candidate):
    for row in candidate.get("rows", []):
        receipt = row.get("receipt")
        if type(receipt) is not dict:
            raise ValueError("runtime receipt missing")
        for summary, raw in (("outcome", "outcome"),
                             ("reason", "reason"),
                             ("completed_transitions", "completed_transitions")):
            if row.get(summary) != receipt.get(raw):
                raise ValueError(f"candidate summary diverges from receipt: {summary}")
    result = audit_v1(candidate)
    result["schema"] = "compiled-handle-graph-composition-audit-v2"
    result["audit_delta"] = "cross-checks duplicated row outcome/reason/transition fields against raw runtime receipts"
    return result


if __name__ == "__main__":
    result = audit(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2, sort_keys=True))
