"""CPU-only three-axis construction-seed independence probe for #5139."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE))
from make_dataset import build  # noqa: E402
from audit_sampler import audit_support_selection  # noqa: E402

FORMAL, FORMAL_ALT = 903520260929, 903520260931
SUPPORT, SUPPORT_ALT = 903520260930, 903520260932
ALLOCATION = "qwen5139-seed-axis-construction-only"

base = build(FORMAL, SUPPORT, ALLOCATION)
formal_alt = build(FORMAL_ALT, SUPPORT, ALLOCATION)
support_alt = build(FORMAL, SUPPORT_ALT, ALLOCATION)
allocation_alt = build(FORMAL, SUPPORT, ALLOCATION + "-metadata")

checks = {
    "formal_seed_change_preserves_support_pool": base["support_pool"] == formal_alt["support_pool"],
    "formal_seed_change_preserves_support_arms": base["supports"] == formal_alt["supports"],
    "formal_seed_change_changes_heldout_pool": base["heldout_pool"] != formal_alt["heldout_pool"],
    "formal_seed_change_changes_heldout_selection": base["heldout"] != formal_alt["heldout"],
    "support_seed_change_changes_support_pool": base["support_pool"] != support_alt["support_pool"],
    "support_seed_change_changes_support_arms": base["supports"] != support_alt["supports"],
    "support_seed_change_preserves_heldout_pool": base["heldout_pool"] == support_alt["heldout_pool"],
    "support_seed_change_preserves_heldout_selection": base["heldout"] == support_alt["heldout"],
    "allocation_label_changes_only_metadata": all(
        base[k] == allocation_alt[k] for k in base if k != "allocation"
    ) and base["allocation"] != allocation_alt["allocation"],
    "support_audit_clean_for_all": all(
        audit_support_selection(ds) == [] for ds in (base, formal_alt, support_alt)
    ),
}

def canonical_hash(obj: dict) -> str:
    raw = (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()

result = {
    "status": "PASS_CONSTRUCTION_SEED_AXIS_INDEPENDENCE" if all(checks.values()) else "STOP_CONSTRUCTION_SEED_AXIS_INDEPENDENCE",
    "seeds": {"formal": FORMAL, "formal_alternate": FORMAL_ALT,
              "support": SUPPORT, "support_alternate": SUPPORT_ALT},
    "dataset_hashes": {"base": canonical_hash(base), "formal_alternate": canonical_hash(formal_alt),
                       "support_alternate": canonical_hash(support_alt), "allocation_label_alternate": canonical_hash(allocation_alt)},
    "checks": checks,
    "scope": "synthetic CPU-only construction probe; no model, CUDA, GPU, Docker, fit, or formal allocation",
}
out = Path(__file__).with_name("result.json")
out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
if not all(checks.values()):
    raise SystemExit(1)
