import importlib.util
from pathlib import Path


root = Path(__file__).parent
spec = importlib.util.spec_from_file_location("runner", root / "runner.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
audit_spec = importlib.util.spec_from_file_location("audit", root / "audit.py")
audit = importlib.util.module_from_spec(audit_spec)
audit_spec.loader.exec_module(audit)

doc = runner.build_raw()
result = audit.audit_document(doc)
assert result["errors"] == [], result["errors"]
assert result["equal_time_raw_gt_compressed"] is True
assert result["compressed_now_gt_raw_delayed"] is True
assert all(not row["admitted"] and not row["unsafe_effect"] for row in doc["compressed_irreversible_probes"])
assert len(result["corruptions"]) == 5 and all(row["rejected"] for row in result["corruptions"])
print("PREFLIGHT_PASS", result["utility_by_arm"])
