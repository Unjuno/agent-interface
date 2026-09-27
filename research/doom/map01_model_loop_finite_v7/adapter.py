"""Fresh successor aligning the final submit-send timestamp to runtime time."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V6_PATH = HERE.parent / "map01_model_loop_finite_v6" / "adapter.py"
spec = importlib.util.spec_from_file_location("map01_finite_v6_adapter", V6_PATH)
v6 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v6)
base = v6.base

SEND_BOUNDARY_REPLACEMENT = (
    (
'''before=dict(latest);event_start=len(all_events);clock_ns=time.perf_counter_ns()
            steps=compile_commands(commands)''',
'''before=dict(latest);event_start=len(all_events)
            steps=compile_commands(commands)
            _send_clock_samples=[]
            for _ in range(3):
                _h1=time.perf_counter_ns()
                process.stdin.write('{"op":"clock"}\\n');process.stdin.flush()
                _clock=wait(lambda r:r.get("event")=="clock")
                _h2=time.perf_counter_ns()
                _send_clock_samples.append({"host_send_ns":_h1,
                    "runtime_ns":_clock["runtime_ns"],"host_receive_ns":_h2,
                    "offset_lower_ns":_clock["runtime_ns"]-_h2,
                    "offset_upper_ns":_clock["runtime_ns"]-_h1})
            _send_offset_lower=min(x["offset_lower_ns"] for x in _send_clock_samples)
            _send_offset_upper=max(x["offset_upper_ns"] for x in _send_clock_samples)
            if _send_offset_upper-_send_offset_lower>1_000_000_000:
                raise RuntimeError("HOLD_INFRASTRUCTURE: submit-send clock interval exceeds 1s")
            globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_send_offset_lower
            _send_log_path=runtime/"submit-send-clock-translations.jsonl"
            clock_ns=time.perf_counter_ns()
            _runtime_sent_ns=clock_ns+_send_offset_lower
            if _runtime_sent_ns<_validity_decided_runtime_ns:
                raise RuntimeError("HOLD_INFRASTRUCTURE: translated submit send precedes current-validity decision")
            if clock_ns+25_000_000_000-time.perf_counter_ns()<5_000_000_000:
                raise RuntimeError("HOLD_INFRASTRUCTURE: submit lease margin below 5s")
            with _send_log_path.open("a") as _f:
                _f.write(json.dumps({"id":identifier,"host_sent_ns":clock_ns,
                    "runtime_sent_ns":_runtime_sent_ns,
                    "offset_lower_ns":_send_offset_lower,
                    "offset_upper_ns":_send_offset_upper,
                    "validity_decided_runtime_ns":_validity_decided_runtime_ns,
                    "samples":_send_clock_samples},sort_keys=True)+"\\n")'''),
    ('running_guard.admit_program(\n                program_binding,{"command":submit_command,"sent_ns":clock_ns},',
     'running_guard.admit_program(\n                program_binding,{"command":submit_command,"sent_ns":_runtime_sent_ns},'),
)

ZERO_DECISION_SELFTEST = '''
    if args.iterations == 0:
        _stage2_samples=[]
        for _ in range(3):
            _h1=time.perf_counter_ns()
            process.stdin.write('{"op":"clock"}\\n');process.stdin.flush()
            _clock=wait(lambda r:r.get("event")=="clock")
            _h2=time.perf_counter_ns()
            _stage2_samples.append({"host_send_ns":_h1,"runtime_ns":_clock["runtime_ns"],
                "host_receive_ns":_h2,
                "offset_lower_ns":_clock["runtime_ns"]-_h2,
                "offset_upper_ns":_clock["runtime_ns"]-_h1})
        _stage2_lower=min(x["offset_lower_ns"] for x in _stage2_samples)
        _stage2_upper=max(x["offset_upper_ns"] for x in _stage2_samples)
        if _stage2_upper-_stage2_lower>1_000_000_000:
            raise RuntimeError("HOLD_INFRASTRUCTURE: zero-decision send clock interval exceeds 1s")
        globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_stage2_lower
        _stage2_host_sent=time.perf_counter_ns()
        _stage2_runtime_sent=_stage2_host_sent+_stage2_lower
        _stage2_id="v7-zero-decision-observe-only"
        _stage2_command={"op":"submit","id":_stage2_id,
            "expected_sequence":latest["sequence"],
            "valid_until_ns":_stage2_host_sent+25_000_000_000,
            "steps":[{"op":"observe"}]}
        process.stdin.write(json.dumps(_stage2_command)+"\\n");process.stdin.flush()
        _stage2_accepted=wait(lambda r:r["event"] in ("accepted","rejected") and
            (r.get("id")==_stage2_id or r["event"]=="rejected"))
        if (_stage2_accepted["event"]!="accepted" or
                _stage2_accepted["accepted_ns"]<_stage2_runtime_sent):
            raise RuntimeError("HOLD_INFRASTRUCTURE: zero-decision submit admission/order failed: "+repr(_stage2_accepted))
        _stage2_terminal=wait(lambda r:r["event"]=="terminal" and r.get("id")==_stage2_id)
        _stage2_release=_stage2_terminal.get("release",{})
        if (_stage2_terminal.get("status")!="completed" or
                _stage2_release.get("verified") is not True or
                _stage2_release.get("keys_down")!=[] or
                _stage2_release.get("buttons_down")!=[]):
            raise RuntimeError("HOLD_INFRASTRUCTURE: zero-decision owner cleanup unverified")
        (runtime/"submit-clock-zero-decision.json").write_text(json.dumps({
            "sample_count":len(_stage2_samples),"same_session":True,
            "offset_lower_ns":_stage2_lower,"offset_upper_ns":_stage2_upper,
            "uncertainty_width_ns":_stage2_upper-_stage2_lower,
            "host_sent_ns":_stage2_host_sent,"runtime_sent_ns":_stage2_runtime_sent,
            "executor_accepted_ns":_stage2_accepted["accepted_ns"],
            "acceptance_minus_translated_send_ns":_stage2_accepted["accepted_ns"]-_stage2_runtime_sent,
            "samples":_stage2_samples,"accepted":_stage2_accepted,
            "terminal":_stage2_terminal,"input_authority":"observe_only",
            "model_turns":0},indent=2)+"\\n")
'''
_LEASE_WRAPPER_ANCHOR = 'runtime/"lease-deadline-translations.jsonl")'
base.REPLACEMENTS = tuple(base.REPLACEMENTS) + (
    (_LEASE_WRAPPER_ANCHOR, _LEASE_WRAPPER_ANCHOR + ZERO_DECISION_SELFTEST),
)

base.REPLACEMENTS = tuple(base.REPLACEMENTS) + SEND_BOUNDARY_REPLACEMENT


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
