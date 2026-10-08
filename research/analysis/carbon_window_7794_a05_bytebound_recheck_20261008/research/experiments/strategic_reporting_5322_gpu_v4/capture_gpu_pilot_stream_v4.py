#!/usr/bin/env python3
"""Memory-only pilot runner; emits a durable event after each completed call."""
import base64,contextlib,hashlib,io,json,sys
from pathlib import Path

ROOT=Path.cwd()/"research"/"experiments"/"strategic_reporting_5322_gpu_v4"
EXPECTED={"pilot":"720fbcfeb06085ff500e780f1fbf7459f459e190656b7d733e4421b6f35d2827","audit":"62242eaa2a86fc31138cbcf4d2345c63e083f548413a95807ac6d02ce4231129"}
if len(sys.argv)!=3: raise SystemExit("STOP: supply frozen pilot and auditor base64")
pilot_source=base64.b64decode(sys.argv[1]); audit_source=base64.b64decode(sys.argv[2])
for name,source in (("pilot",pilot_source),("audit",audit_source)):
    actual=hashlib.sha256(source).hexdigest()
    if actual!=EXPECTED[name]: raise SystemExit(f"STOP: {name} hash mismatch {actual}")

LIVE_STDOUT=sys.stdout
FILES={}; latest_calls=[]; emitted_calls=0; emitted_rows=0
def memory_mkdir(self,*args,**kwargs): return None
def memory_write_text(self,data,*args,**kwargs):
    global latest_calls,emitted_calls,emitted_rows
    value=str(data); FILES[self.name]=value
    if self.name=="calls.json": latest_calls=json.loads(value)
    if self.name=="raw.jsonl":
        rows=[json.loads(x) for x in value.splitlines() if x]
        while emitted_calls<len(latest_calls):
            call=latest_calls[emitted_calls]
            new_rows=rows[emitted_rows:emitted_rows+16]
            raw_lines=value.splitlines()[emitted_rows:emitted_rows+16]
            event={"call_index":emitted_calls+1,"call":call,"rows":new_rows,"raw_lines":raw_lines}
            LIVE_STDOUT.write("CALL_EVENT:"+json.dumps(event,sort_keys=True,separators=(",",":"))+"\\n"); LIVE_STDOUT.flush()
            emitted_calls+=1; emitted_rows+=len(new_rows)
            ack=sys.stdin.readline().strip()
            if ack!=f"ACK {emitted_calls}":
                FILES["capture_stop.json"]=json.dumps({"status":"STOP_NO_ACK","expected":f"ACK {emitted_calls}","observed":ack})+"\\n"
                raise SystemExit("STOP: GitHub durability ACK missing; do not start another model call")
    return len(value)
def memory_read_text(self,*args,**kwargs): return FILES[self.name]
def memory_read_bytes(self): return FILES[self.name].encode("utf-8")
Path.mkdir=memory_mkdir; Path.write_text=memory_write_text
Path.read_text=memory_read_text; Path.read_bytes=memory_read_bytes

out=io.StringIO(); pilot_exit=None
sys.argv=[str(ROOT/"gpu_model_pilot_v4.py"),"--output","memory-gpu-pilot-04"]
try:
    with contextlib.redirect_stdout(out):
        exec(compile(pilot_source.decode("utf-8"),str(ROOT/"gpu_model_pilot_v4.py"),"exec"),
             {"__name__":"__main__","__file__":str(ROOT/"gpu_model_pilot_v4.py")})
except SystemExit as exc: pilot_exit=exc.code
except BaseException as exc:
    pilot_exit="EXCEPTION"; FILES["runner_exception.txt"]=repr(exc)
FILES["pilot_stdout.txt"]=out.getvalue()
audit_exit=None; audit_out=io.StringIO()
if "RESULT_STATUS.json" in FILES:
    sys.argv=[str(ROOT/"audit_gpu_model_pilot_v4.py"),"memory-gpu-pilot-04"]
    try:
        with contextlib.redirect_stdout(audit_out):
            exec(compile(audit_source.decode("utf-8"),str(ROOT/"audit_gpu_model_pilot_v4.py"),"exec"),
                 {"__name__":"__main__","__file__":str(ROOT/"audit_gpu_model_pilot_v4.py")})
    except SystemExit as exc: audit_exit=exc.code
    except BaseException as exc:
        audit_exit="EXCEPTION"; FILES["audit_exception.txt"]=repr(exc)
FILES["audit_stdout.txt"]=audit_out.getvalue()
FINAL_KEYS=("inventory.json","runtime_evidence.json","summary.json","RESULT_STATUS.json",
    "AUDIT.json","STOP.json","failed_call.json","pilot_stdout.txt","audit_stdout.txt")
final_files={key:FILES[key] for key in FINAL_KEYS if key in FILES}
LIVE_STDOUT.write("FINAL_EVENT:"+json.dumps({"pilot_exit":pilot_exit,"audit_exit":audit_exit,
    "files":final_files},sort_keys=True,separators=(",",":"))+"\\n"); LIVE_STDOUT.flush()
