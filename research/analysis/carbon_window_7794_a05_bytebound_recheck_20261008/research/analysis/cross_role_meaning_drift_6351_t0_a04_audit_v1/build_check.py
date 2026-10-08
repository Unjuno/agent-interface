import json
from auditor import audit

result = audit("input/raw.json", "input/candidate.json", "input/oracle.json")
assert result["all_rows_match"]
assert all(result["mutations"].values())
assert sum(len(r["fields"]) for r in result["rows"]) == 56
print("BUILD_PASS rows=8 role_fields=56 mutations=5")
