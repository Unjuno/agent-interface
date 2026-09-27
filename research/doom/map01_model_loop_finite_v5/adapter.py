"""Fresh MAP01 successor: runtime-clock calibration and host lease translation."""
from __future__ import annotations

import importlib.util
import os
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE.parent / "map01_model_loop_finite_v3" / "adapter.py"
spec = importlib.util.spec_from_file_location("map01_finite_v3_adapter", BASE_PATH)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(base)

CALIBRATION_INJECTION = 'latest = wait(lambda r:r["event"] == "observation")\n' + textwrap.indent(r'''
import os
# Calibrate against this exact running session using its supported clock op.
_clock_samples=[]
for _clock_i in range(24):
    _clock_send_ns=time.perf_counter_ns()
    process.stdin.write('{"op":"clock"}\n'); process.stdin.flush()
    _clock_row=wait(lambda r:r.get("event")=="clock")
    _clock_recv_ns=time.perf_counter_ns()
    _clock_samples.append({"host_send_ns":_clock_send_ns,
        "runtime_ns":_clock_row["runtime_ns"],"host_receive_ns":_clock_recv_ns,
        "offset_lower_ns":_clock_row["runtime_ns"]-_clock_recv_ns,
        "offset_upper_ns":_clock_row["runtime_ns"]-_clock_send_ns})
_lease_offset_lower=min(x["offset_lower_ns"] for x in _clock_samples)
_lease_offset_upper=max(x["offset_upper_ns"] for x in _clock_samples)
_lease_uncertainty_ns=_lease_offset_upper-_lease_offset_lower
if _lease_uncertainty_ns > 1_000_000_000:
    raise RuntimeError("HOLD_INFRASTRUCTURE: same-session clock offset interval exceeds 1s")
(runtime/"lease-clock-calibration.json").write_text(json.dumps({
    "samples":_clock_samples,"offset_lower_ns":_lease_offset_lower,
    "offset_upper_ns":_lease_offset_upper,"uncertainty_ns":_lease_uncertainty_ns,
    "sample_count":len(_clock_samples),"same_session":True},indent=2))
_clock_controls=[]
def _clock_submit(identifier,host_deadline,expected):
    _runtime_deadline=host_deadline+_lease_offset_lower
    _wire={"op":"submit","id":identifier,
        "expected_sequence":latest["sequence"],
        "valid_until_ns":_runtime_deadline,"steps":[{"op":"observe"}]}
    process.stdin.write(json.dumps(_wire)+"\n");process.stdin.flush()
    _reply=wait(lambda r:r["event"] in ("accepted","rejected") and
                (r.get("id")==identifier or r["event"]=="rejected"))
    if _reply["event"]!=expected:
        raise RuntimeError("HOLD_INFRASTRUCTURE: same-session lease control mismatch: "
                           +repr(_reply))
    _clock_controls.append({"id":identifier,"host_deadline_ns":host_deadline,
        "runtime_deadline_ns":_runtime_deadline,"result":_reply["event"],
        "reason":_reply.get("reason")})
    return _reply
_clock_reply=_clock_submit("clock-preflight-live",
    time.perf_counter_ns()+25_000_000_000,"accepted")
wait(lambda r:r["event"]=="terminal" and r.get("id")=="clock-preflight-live")
_clock_submit("clock-preflight-expired",
    time.perf_counter_ns()-1_000_000,"rejected")
_clock_submit("clock-preflight-over30",
    time.perf_counter_ns()+31_000_000_000,"rejected")
_clock_short_deadline=time.perf_counter_ns()+300_000_000
time.sleep(0.4)
_clock_submit("clock-preflight-delayed",_clock_short_deadline,"rejected")
(runtime/"lease-clock-calibration.json").write_text(json.dumps({
    "samples":_clock_samples,"offset_lower_ns":_lease_offset_lower,
    "offset_upper_ns":_lease_offset_upper,"uncertainty_ns":_lease_uncertainty_ns,
    "sample_count":len(_clock_samples),"same_session":True,
    "synthetic_controls":_clock_controls},indent=2))
class _LeaseClockStdin:
    def __init__(self,stream,offset,log_path):
        self.stream,self.offset,self.log_path=stream,offset,log_path
    def write(self,line):
        command=json.loads(line)
        if "valid_until_ns" in command:
            host_deadline=command["valid_until_ns"]
            _samples=[]
            for _ in range(3):
                _h1=time.perf_counter_ns()
                self.stream.write('{"op":"clock"}\n');self.stream.flush()
                _clock=wait(lambda r:r.get("event")=="clock")
                _h2=time.perf_counter_ns()
                _samples.append({"host_send_ns":_h1,"runtime_ns":_clock["runtime_ns"],
                    "host_receive_ns":_h2,
                    "offset_lower_ns":_clock["runtime_ns"]-_h2,
                    "offset_upper_ns":_clock["runtime_ns"]-_h1})
            _lower=min(x["offset_lower_ns"] for x in _samples)
            _upper=max(x["offset_upper_ns"] for x in _samples)
            if _upper-_lower>1_000_000_000:
                raise RuntimeError("HOLD_INFRASTRUCTURE: per-command clock interval exceeds 1s")
            _remaining=host_deadline-time.perf_counter_ns()
            if _remaining<5_000_000_000:
                raise RuntimeError("HOLD_INFRASTRUCTURE: host lease margin below 5s")
            command["valid_until_ns"]=host_deadline+_lower
            with self.log_path.open("a") as _f:
                _f.write(json.dumps({"id":command.get("id"),
                    "host_deadline_ns":host_deadline,
                    "runtime_deadline_ns":command["valid_until_ns"],
                "offset_lower_ns":_lower,"offset_upper_ns":_upper,
                "calibration_samples":_samples,
                    "translated_at_host_ns":time.perf_counter_ns()},sort_keys=True)+"\n")
            line=json.dumps(command)+"\n"
        return self.stream.write(line)
    def flush(self): return self.stream.flush()
process.stdin=_LeaseClockStdin(process.stdin,_lease_offset_lower,
                               runtime/"lease-deadline-translations.jsonl")
if os.environ.get("AGENT_CLOCK_SELFTEST")=="1":
    _test_id="clock-wrapper-selftest"
    _test_command={"op":"submit","id":_test_id,
        "expected_sequence":latest["sequence"],
        "valid_until_ns":time.perf_counter_ns()+25_000_000_000,
        "steps":[{"op":"observe"}]}
    process.stdin.write(json.dumps(_test_command)+"\n");process.stdin.flush()
    _test_ack=wait(lambda r:r["event"] in ("accepted","rejected") and
                   (r.get("id")==_test_id or r["event"]=="rejected"))
    if _test_ack["event"]!="accepted":
        raise RuntimeError("HOLD_INFRASTRUCTURE: per-command translation self-test rejected: "
                           +repr(_test_ack))
    wait(lambda r:r["event"]=="terminal" and r.get("id")==_test_id)
''', "    ")

anchor = 'latest = wait(lambda r:r["event"] == "observation")'
base.REPLACEMENTS = tuple(base.REPLACEMENTS) + ((anchor, CALIBRATION_INJECTION),)


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
