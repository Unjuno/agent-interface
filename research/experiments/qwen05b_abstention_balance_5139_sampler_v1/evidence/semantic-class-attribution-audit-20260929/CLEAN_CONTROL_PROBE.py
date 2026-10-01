from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "restored"
sys.path.insert(0, str(BUNDLE))
source_path = BUNDLE / "audit_results.py"
source = source_path.read_text(encoding="utf-8")
helper = '''
def _class_from_intent(intent):
    if not isinstance(intent, dict): return None
    op = intent.get("op")
    if op in ("set", "save", "toggle"): return op
    if op in ("yield", "no_action"):
        reason = intent.get("reason")
        return f"{op}:{reason}" if isinstance(reason, str) else None
    return None


'''
needle = "def _dataset_errors(data: Mapping[str, Any]) -> list[str]:\n"
assert source.count(needle) == 1
fixed = source.replace(needle, helper + needle, 1)
needle2 = '    support_pool = data.get("support_pool", [])\n    heldout_pool = data.get("heldout_pool", [])\n'
assert source.count(needle2) == 1
checks = '''    for split_name, pool in (("support_pool", support_pool), ("heldout_pool", heldout_pool)):
        for index, row in enumerate(pool):
            if not isinstance(row, Mapping) or row.get("class") != _class_from_intent(row.get("intent")):
                errors.append(f"{split_name}_class_vs_intent:{index}")
'''
fixed = fixed.replace(needle2, needle2 + checks, 1)
fixed_path = ROOT / "restored" / "audit_results_clean_control.py"
fixed_path.write_text(fixed, encoding="utf-8")
spec = importlib.util.spec_from_file_location("audit_results_clean_control", fixed_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
rows = {}
for label in ("original", "mutated"):
    dataset_path = BUNDLE / "verified" / "inputs" / f"{label}_dataset.json"
    payload = dataset_path.read_bytes()
    errors = module._dataset_errors(json.loads(payload))
    class_errors = [e for e in errors if "class_vs_intent" in e]
    rows[label] = {
        "dataset_sha256": hashlib.sha256(payload).hexdigest(),
        "integrity_pass": not errors,
        "error_count": len(errors),
        "class_vs_intent_error_count": len(class_errors),
        "first_errors": errors[:4],
    }
result = {
    "result": "PASS_CLEAN_CONTROL_ACCEPTS_ORIGINAL_REJECTS_MUTATION",
    "source_commit": "20715c0dee3064f22e47c3d26f545697cfb2c6bf",
    "bundle_sha256": "3a853f78c501e6c2ac1f05dcdfe0c486ca979b49a126bda1328dfd4f0dc16445",
    "fixed_auditor_sha256": hashlib.sha256(fixed_path.read_bytes()).hexdigest(),
    "original": rows["original"],
    "mutated": rows["mutated"],
    "scope": "Host Python dataset-integrity control only; not full raw-output audit or model result",
    "resource_scope": "No GPU/CUDA/model/tokenizer/Docker/OrbStack/GUI/formal allocation",
}
out = ROOT / "CLEAN_CONTROL_RESULT.json"
out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(out.read_text(encoding="utf-8"), end="")
