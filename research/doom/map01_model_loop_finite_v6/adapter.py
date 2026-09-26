"""Fresh MAP01 successor: align action-freshness timestamps with runtime clock."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE.parent / "map01_model_loop_finite_v5" / "adapter.py"
spec = importlib.util.spec_from_file_location("map01_finite_v5_adapter", BASE_PATH)
v5 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v5)
base = v5.base

HELPER = '''_RUNTIME_CLOCK_OFFSET_LOWER = None
def runtime_clock_ns():
    if type(_RUNTIME_CLOCK_OFFSET_LOWER) is not int:
        raise RuntimeError("HOLD_INFRASTRUCTURE: runtime clock offset unavailable")
    return time.perf_counter_ns() + _RUNTIME_CLOCK_OFFSET_LOWER

def main():'''

MONITOR_CLOCK_REPLACEMENT = (
    'decided_ns = time.perf_counter_ns() if decided_ns is None else decided_ns',
    'decided_ns = runtime_clock_ns() if decided_ns is None else decided_ns',
)

LEASE_CLOCK_GLOBAL_REPLACEMENT = (
    'command["valid_until_ns"]=host_deadline+_lower',
    'command["valid_until_ns"]=host_deadline+_lower\n'
    '                globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_lower',
)

FINAL_ADMISSION_REPLACEMENT = (
'''final_action_admission=final_admission_from_planner_result(
            planner_result,planner_terminal_observed_ns,
            invalidation,time.perf_counter_ns())''',
'''_decision_clock_samples=[]
        for _ in range(3):
            _h1=time.perf_counter_ns()
            process.stdin.write('{"op":"clock"}\\n');process.stdin.flush()
            _clock=wait(lambda r:r.get("event")=="clock")
            _h2=time.perf_counter_ns()
            _decision_clock_samples.append({"host_send_ns":_h1,
                "runtime_ns":_clock["runtime_ns"],"host_receive_ns":_h2,
                "offset_lower_ns":_clock["runtime_ns"]-_h2,
                "offset_upper_ns":_clock["runtime_ns"]-_h1})
        _decision_offset_lower=min(x["offset_lower_ns"] for x in _decision_clock_samples)
        _decision_offset_upper=max(x["offset_upper_ns"] for x in _decision_clock_samples)
        if _decision_offset_upper-_decision_offset_lower>1_000_000_000:
            raise RuntimeError("HOLD_INFRASTRUCTURE: action-decision clock interval exceeds 1s")
        globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_decision_offset_lower
        _planner_terminal_host_ns=planner_terminal_observed_ns
        _controller_decided_host_ns=time.perf_counter_ns()
        _planner_terminal_runtime_ns=_planner_terminal_host_ns+_decision_offset_lower
        _controller_decided_runtime_ns=_controller_decided_host_ns+_decision_offset_lower
        with (runtime/"action-freshness-clock-translations.jsonl").open("a") as _f:
            _f.write(json.dumps({"iteration":index,
                "planner_terminal_host_ns":_planner_terminal_host_ns,
                "planner_terminal_runtime_ns":_planner_terminal_runtime_ns,
                "controller_decided_host_ns":_controller_decided_host_ns,
                "controller_decided_runtime_ns":_controller_decided_runtime_ns,
                "offset_lower_ns":_decision_offset_lower,
                "offset_upper_ns":_decision_offset_upper,
                "samples":_decision_clock_samples},sort_keys=True)+"\\n")
        final_action_admission=final_admission_from_planner_result(
            planner_result,_planner_terminal_runtime_ns,
            invalidation,_controller_decided_runtime_ns)''')

PREPARE_VALIDITY_REPLACEMENT = (
'''final_action_admission=prepare_action_admission(
            final_action_admission,action,action["action_validity"][0],
            source_health_signal,source_ammo_signal,
            current_health_signal,current_ammo_signal,time.perf_counter_ns())''',
'''_validity_clock_samples=[]
        for _ in range(3):
            _h1=time.perf_counter_ns()
            process.stdin.write('{"op":"clock"}\\n');process.stdin.flush()
            _clock=wait(lambda r:r.get("event")=="clock")
            _h2=time.perf_counter_ns()
            _validity_clock_samples.append({"host_send_ns":_h1,
                "runtime_ns":_clock["runtime_ns"],"host_receive_ns":_h2,
                "offset_lower_ns":_clock["runtime_ns"]-_h2,
                "offset_upper_ns":_clock["runtime_ns"]-_h1})
        _validity_offset_lower=min(x["offset_lower_ns"] for x in _validity_clock_samples)
        _validity_offset_upper=max(x["offset_upper_ns"] for x in _validity_clock_samples)
        if _validity_offset_upper-_validity_offset_lower>1_000_000_000:
            raise RuntimeError("HOLD_INFRASTRUCTURE: action-validity clock interval exceeds 1s")
        globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_validity_offset_lower
        _validity_decided_host_ns=time.perf_counter_ns()
        _validity_decided_runtime_ns=_validity_decided_host_ns+_validity_offset_lower
        with (runtime/"action-freshness-clock-translations.jsonl").open("a") as _f:
            _f.write(json.dumps({"iteration":index,"stage":"freshness",
                "controller_decided_host_ns":_validity_decided_host_ns,
                "controller_decided_runtime_ns":_validity_decided_runtime_ns,
                "offset_lower_ns":_validity_offset_lower,
                "offset_upper_ns":_validity_offset_upper,
                "samples":_validity_clock_samples},sort_keys=True)+"\\n")
        final_action_admission=prepare_action_admission(
            final_action_admission,action,action["action_validity"][0],
            source_health_signal,source_ammo_signal,
            current_health_signal,current_ammo_signal,_validity_decided_runtime_ns)''')

base.REPLACEMENTS = tuple(base.REPLACEMENTS) + (
    ("def main():", HELPER),
    MONITOR_CLOCK_REPLACEMENT,
    LEASE_CLOCK_GLOBAL_REPLACEMENT,
    FINAL_ADMISSION_REPLACEMENT,
    PREPARE_VALIDITY_REPLACEMENT,
)


def main() -> None:
    module = base.load_controller()
    if "--prepare-only" in sys.argv:
        target=Path(sys.argv[sys.argv.index("--prepare-only")+1]).resolve()
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(module._freshstart_effective_source,encoding="utf-8")
        print(f"effective_controller_sha256={module._freshstart_sha256}")
        print(f"effective_controller_path={target}")
        return
    module.main()


if __name__ == "__main__":
    main()
