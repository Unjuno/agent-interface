#!/usr/bin/env python3
"""Memory-only row-framed GPU pilot runner. Each call blocks until durable ACK."""
import base64, contextlib, hashlib, io, json, sys, types, zlib
from pathlib import Path

ROOT = Path.cwd() / "research" / "experiments" / "strategic_reporting_5322_gpu_v5"
EXPECTED = {"pilot": "1f53dd5007afe54d523448126d6cff71f24a29d07e3fd38f5a78348efaa74a36", "audit": "9e3d0c89ac4654c0d2d5d28b47ed7c5434e4ba52743a1f47ee82ba243ebd1c79", "transport": "982034983289a7c2d5403eae355e148920d64b4fa6f2efa42bc6ba8fad490df1"}
arguments = sys.argv[1:]
synthetic_smoke = "--synthetic-smoke" in arguments
arguments = [x for x in arguments if x != "--synthetic-smoke"]
if len(arguments) != 3:
    raise SystemExit("STOP: supply frozen pilot, auditor, and transport sources")
def decode_source(value):
    if value.startswith("z:"):
        return zlib.decompress(base64.b64decode(value[2:]))
    return base64.b64decode(value)
pilot_source, audit_source, transport_source = (decode_source(x) for x in arguments)
sources = {"pilot": pilot_source, "audit": audit_source, "transport": transport_source}
for name, source in sources.items():
    actual = hashlib.sha256(source).hexdigest()
    if actual != EXPECTED[name]:
        raise SystemExit(f"STOP: {name} source hash mismatch {actual}")
transport = types.ModuleType("row_frames")
exec(compile(transport_source.decode("utf-8"), "row_frames.py", "exec"), transport.__dict__)

if synthetic_smoke:
    for call_index in range(1, 7):
        payload = json.dumps({"rows": [{"case_id": i, "text": "x" * 384}
                                      for i in range(16)]},
                             separators=(",", ":")).encode("utf-8")
        for frame in transport.encode_call(call_index, payload):
            sys.stdout.write(frame + "\n")
            sys.stdout.flush()
        ack = sys.stdin.readline().strip()
        if ack != f"ACK {call_index}":
            final = json.dumps({"status": "STOP_NO_ACK", "call": call_index,
                                "observed": ack}, sort_keys=True,
                               separators=(",", ":")).encode("utf-8")
            for frame in transport.encode_call(0, final):
                sys.stdout.write(frame + "\n")
                sys.stdout.flush()
            raise SystemExit("STOP: synthetic ACK mismatch")
    final = json.dumps({"status": "SYNTHETIC_TRANSPORT_PASS",
                        "completed_call_events": 6, "model_calls": 0},
                       sort_keys=True, separators=(",", ":")).encode("utf-8")
    for frame in transport.encode_call(0, final):
        sys.stdout.write(frame + "\n")
        sys.stdout.flush()
    raise SystemExit(0)

LIVE_STDOUT = sys.stdout
FILES = {}
latest_calls = []
emitted_calls = 0
emitted_rows = 0

def memory_mkdir(self, *args, **kwargs):
    return None

def memory_write_text(self, data, *args, **kwargs):
    global latest_calls, emitted_calls, emitted_rows
    value = str(data)
    FILES[self.name] = value
    if self.name == "calls.json":
        latest_calls = json.loads(value)
    if self.name == "raw.jsonl":
        rows = [json.loads(x) for x in value.splitlines() if x]
        while emitted_calls < len(latest_calls):
            call = latest_calls[emitted_calls]
            raw_lines = value.splitlines()[emitted_rows:emitted_rows + 16]
            new_rows = rows[emitted_rows:emitted_rows + 16]
            event = {"call_index": emitted_calls + 1, "call": call,
                     "rows": new_rows, "raw_lines": raw_lines}
            payload = json.dumps(event, ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":")).encode("utf-8")
            for frame in transport.encode_call(emitted_calls + 1, payload):
                LIVE_STDOUT.write(frame + "\n")
                LIVE_STDOUT.flush()
            emitted_calls += 1
            emitted_rows += len(new_rows)
            ack = sys.stdin.readline().strip()
            if ack != f"ACK {emitted_calls}":
                FILES["capture_stop.json"] = json.dumps(
                    {"status": "STOP_NO_ACK", "expected": f"ACK {emitted_calls}",
                     "observed": ack}) + "\n"
                raise SystemExit("STOP: durable GitHub ACK missing; do not start another call")
    return len(value)

def memory_read_text(self, *args, **kwargs):
    return FILES[self.name]

def memory_read_bytes(self):
    return FILES[self.name].encode("utf-8")

Path.mkdir = memory_mkdir
Path.write_text = memory_write_text
Path.read_text = memory_read_text
Path.read_bytes = memory_read_bytes

out = io.StringIO()
pilot_exit = None
sys.argv = [str(ROOT / "gpu_model_pilot_v5.py"), "--output", "memory-gpu-pilot-05"]
try:
    with contextlib.redirect_stdout(out):
        exec(compile(pilot_source.decode("utf-8"), str(ROOT / "gpu_model_pilot_v5.py"), "exec"),
             {"__name__": "__main__", "__file__": str(ROOT / "gpu_model_pilot_v5.py")})
except SystemExit as exc:
    pilot_exit = exc.code
except BaseException as exc:
    pilot_exit = "EXCEPTION"
    FILES["runner_exception.txt"] = repr(exc)
FILES["pilot_stdout.txt"] = out.getvalue()

audit_exit = None
audit_out = io.StringIO()
if "RESULT_STATUS.json" in FILES:
    sys.argv = [str(ROOT / "audit_gpu_model_pilot_v5.py"), "memory-gpu-pilot-05"]
    try:
        with contextlib.redirect_stdout(audit_out):
            exec(compile(audit_source.decode("utf-8"), str(ROOT / "audit_gpu_model_pilot_v5.py"), "exec"),
                 {"__name__": "__main__", "__file__": str(ROOT / "audit_gpu_model_pilot_v5.py")})
    except SystemExit as exc:
        audit_exit = exc.code
    except BaseException as exc:
        audit_exit = "EXCEPTION"
        FILES["audit_exception.txt"] = repr(exc)
FILES["audit_stdout.txt"] = audit_out.getvalue()

keys = ("inventory.json", "runtime_evidence.json", "summary.json", "RESULT_STATUS.json",
        "AUDIT.json", "STOP.json", "failed_call.json", "capture_stop.json",
        "runner_exception.txt", "pilot_stdout.txt", "audit_stdout.txt")
final_files = {key: FILES[key] for key in keys if key in FILES}
event = {"pilot_exit": pilot_exit, "audit_exit": audit_exit, "files": final_files,
         "completed_call_events": emitted_calls, "completed_raw_rows": emitted_rows}
final_payload = json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8")
for frame in transport.encode_call(0, final_payload):
    LIVE_STDOUT.write(frame + "\n")
    LIVE_STDOUT.flush()
