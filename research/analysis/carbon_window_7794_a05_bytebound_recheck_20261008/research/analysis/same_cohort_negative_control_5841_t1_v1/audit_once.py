"""Invoke the independent raw auditor once and exercise two audit mutations."""
import json
from copy import deepcopy
from pathlib import Path

from audit import audit

ROOT = Path(__file__).parent
RESULTS = ROOT / "results"
fixture = json.loads((ROOT / "fixture.json").read_text())
raw = json.loads((RESULTS / "candidate.stdout.json").read_text())
result = audit(fixture, raw)
omitted = deepcopy(raw)
omitted["cases"].pop()
altered = deepcopy(raw)
next(row for row in altered["cases"] if row["case_id"] == "primary_only_fault")["disposition"] = "NO_SIGNAL"
mutation_controls = {
    "omitted_case_rejected": bool(audit(fixture, omitted)["errors"]),
    "false_all_clear_relabel_rejected": bool(audit(fixture, altered)["errors"]),
}
result["mutation_controls"] = mutation_controls
if not all(mutation_controls.values()):
    result["status"] = "FAIL_AUDIT_MUTATION_CONTROL"
(RESULTS / "AUDIT.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
if result["status"] != "PASS_INDEPENDENT_AUDIT":
    raise SystemExit(1)
