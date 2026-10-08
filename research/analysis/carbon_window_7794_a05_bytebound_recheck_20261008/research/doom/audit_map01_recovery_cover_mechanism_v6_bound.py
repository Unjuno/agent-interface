from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path

BASE = Path(__file__).with_name("audit_map01_recovery_cover_mechanism_v6.py")

def _base_audit(root: Path) -> dict:
    spec = importlib.util.spec_from_file_location("map01_v6_base", BASE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.audit(root)

def binding_failures(root: Path) -> list[str]:
    summary = json.loads((root / "summary.json").read_text())
    failures=[]
    for pair in range(1,4):
        p = summary.get(f"pair{pair}", {})
        for arm in ("coast","recovery"):
            key=f"{arm}_no_retained_input_upper_ns"
            pair_value=p.get(key)
            arm_path=root/f"pair{pair}"/arm/"arm-summary.json"
            try:
                arm_value=json.loads(arm_path.read_text())["input_bounds"]["no_retained_input_upper_bound_ns"]
                if type(pair_value) is not int or type(arm_value) is not int or pair_value != arm_value:
                    failures.append(f"pair{pair}:{arm}:{key}:summary_arm_mismatch")
            except (OSError, KeyError, TypeError, ValueError):
                failures.append(f"pair{pair}:{arm}:{key}:summary_arm_missing_or_invalid")
    return failures

def audit(root: Path) -> dict:
    result=dict(_base_audit(root))
    failures=binding_failures(root)
    result["binding_failures"]=failures
    if failures:
        result.update(decision="FAIL", valid_experiment=False, promotable_mechanism_result=False)
    return result
