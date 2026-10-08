from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from audit_sampler import audit_support_selection
from make_dataset import build

saved_raw = Path("dataset.json").read_bytes()
saved = json.loads(saved_raw.decode("utf-8"))
alternate = build(903520260931, 903520260930, "qwen5139-construction-heldout-sentinel-control")
errors = audit_support_selection(alternate)
checks = {
    "alternate_support_pool_same": saved["support_pool"] == alternate["support_pool"],
    "selected_support_arms_same": saved["supports"] == alternate["supports"],
    "heldout_pool_changes": saved["heldout_pool"] != alternate["heldout_pool"],
    "heldout_selection_changes": saved["heldout"] != alternate["heldout"],
    "alternate_support_independent_audit_errors_empty": errors == [],
}
result = {
    "status": "PASS_CONSTRUCTION_SEED_SEPARATION" if all(checks.values()) else "STOP_CONSTRUCTION_SEED_SEPARATION",
    "formal_seed_sentinel_primary": 903520260929,
    "formal_seed_sentinel_alternate": 903520260931,
    "support_seed_sentinel_shared": 903520260930,
    "alternate_dataset_sha256": hashlib.sha256((json.dumps(alternate, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest(),
    "checks": checks,
    "audit_errors": errors,
    "scope": "construction-only seed-separation check; no formal allocation",
}
Path("seed_independence.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
if not all(checks.values()): sys.exit(1)

