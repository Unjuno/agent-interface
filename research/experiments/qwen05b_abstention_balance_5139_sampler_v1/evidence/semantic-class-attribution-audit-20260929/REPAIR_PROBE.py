from __future__ import annotations
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "restored"
sys.path.insert(0, str(BUNDLE))

source_path = BUNDLE / "audit_results.py"
source = source_path.read_text(encoding="utf-8")
helper = '''
def _class_from_intent(intent: Any) -> str | None:
    if not isinstance(intent, Mapping):
        return None
    op = intent.get("op")
    if op in ("set", "save", "toggle"):
        return op
    if op in ("yield", "no_action"):
        reason = intent.get("reason")
        return f"{op}:{reason}" if isinstance(reason, str) else None
    return None


'''
needle = "def _dataset_errors(data: Mapping[str, Any]) -> list[str]:\n"
needle2 = '    support_pool = data.get("support_pool", [])\n    heldout_pool = data.get("heldout_pool", [])\n'
assert source.count(needle) == 1
assert source.count(needle2) == 1
fixed = source.replace(needle, helper + needle, 1)
checks = '''    for split_name, pool in (("support_pool", support_pool), ("heldout_pool", heldout_pool)):
        for index, row in enumerate(pool):
            if not isinstance(row, Mapping):
                errors.append(f"{split_name}_row_not_object:{index}")
            elif row.get("class") != _class_from_intent(row.get("intent")):
                errors.append(f"{split_name}_class_vs_intent:{index}")
'''
fixed = fixed.replace(needle2, needle2 + checks, 1)
fixed_path = BUNDLE / "audit_results_fixed.py"
fixed_path.write_text(fixed, encoding="utf-8")
spec = importlib.util.spec_from_file_location("audit_results_fixed", fixed_path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

dataset_path = BUNDLE / "verified" / "inputs" / "mutated_dataset.json"
raw_path = BUNDLE / "verified" / "inputs" / "raw_outputs.json"
dataset = dataset_path.read_bytes()
raw = json.loads(raw_path.read_text(encoding="utf-8"))
result = module.audit(dataset, raw)
class_errors = [e for e in result["errors"] if "class_vs_intent" in e]
summary = {
    "result": "PASS_REPAIR_CONTROL_REJECTS_LABEL_SWAP",
    "fixed_auditor_integrity_pass": result["integrity_pass"],
    "total_errors": len(result["errors"]),
    "class_vs_intent_error_count": len(class_errors),
    "support_pool_class_vs_intent_errors": sum(e.startswith("support_pool") for e in class_errors),
    "heldout_pool_class_vs_intent_errors": sum(e.startswith("heldout_pool") for e in class_errors),
    "first_class_errors": class_errors[:3],
    "fixed_auditor_sha256": hashlib.sha256(fixed_path.read_bytes()).hexdigest(),
    "mutated_dataset_sha256": hashlib.sha256(dataset).hexdigest(),
    "raw_outputs_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    "source_commit": "20715c0dee3064f22e47c3d26f545697cfb2c6bf",
    "scope": "host-only repair-control probe; no model/GPU/CUDA/Docker work",
}
(ROOT / "REPAIR_RESULT.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\\n", encoding="utf-8")
print(json.dumps(summary, sort_keys=True))

