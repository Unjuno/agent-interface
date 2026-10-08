"""MAP01 adapter using the enriched-receipt-safe final admission translator."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
V10_PATH = HERE.parent / "map01_model_loop_finite_v10" / "adapter.py"
spec = importlib.util.spec_from_file_location("map01_finite_v10_adapter_4544", V10_PATH)
v10 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v10)
base = v10.base

ADMISSION_ANCHOR = '''        final_action_admission=final_admission_from_planner_result(
            planner_result,_planner_terminal_runtime_ns,
            invalidation,_controller_decided_runtime_ns)'''
ADMISSION_TRANSLATION = '''        _runtime_policy_invalidation=None
        if invalidation is not None:
            from clock_translation_v2 import SCHEMA as _policy_clock_schema
            from clock_translation_v2 import translate_invalidation as _translate_policy_invalidation
            _policy_host_receipt=dict(invalidation)
            _policy_host_receipt["timestamp_domain"]="host_monotonic_ns"
            _policy_calibration={"schema":_policy_clock_schema,
                "same_session":True,"host_domain":"host_monotonic_ns",
                "runtime_domain":"runtime_monotonic_ns",
                "samples":_decision_clock_samples}
            _policy_translation,_runtime_policy_invalidation=(
                _translate_policy_invalidation(_policy_host_receipt,_policy_calibration))
            _policy_translation["iteration"]=index
            with (runtime/"policy-invalidation-clock-translations.jsonl").open("a") as _f:
                _f.write(json.dumps(_policy_translation,sort_keys=True)+"\\n")
        final_action_admission=final_admission_from_planner_result(
            planner_result,_planner_terminal_runtime_ns,
            _runtime_policy_invalidation,_controller_decided_runtime_ns)'''


def main() -> None:
    base.REPLACEMENTS = tuple(base.REPLACEMENTS) + ((
        ADMISSION_ANCHOR, ADMISSION_TRANSLATION),)
    v10.main()


if __name__ == "__main__":
    main()
