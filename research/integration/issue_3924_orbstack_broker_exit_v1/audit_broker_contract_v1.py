#!/usr/bin/env python3
"""Independent raw-artifact audit; does not import the runner."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent; OUT=ROOT/"formal"
def load(p): return json.loads(p.read_text())
def errors():
 e=[]; expected={"baseline_exit0":1,"candidate_exit0":0,"candidate_exit7":7,"candidate_timeout":1,"candidate_unavailable":1,"candidate_malformed":1,"candidate_two_queued":0}
 for name,want in expected.items():
  d=OUT/name
  try:
   got=int((d/"process.exit").read_text())
   if got!=want:e.append(f"{name}: process exit {got} != {want}")
  except Exception as x:e.append(f"{name}: missing process exit: {x}")
 for name,receipt in [("baseline_exit0","r1"),("candidate_exit0","r1"),("candidate_exit7","r1"),("candidate_timeout","r1"),("candidate_unavailable","r1"),("candidate_two_queued","r1")]:
  try:
   r=load(OUT/name/f"{receipt}.broker.json")
   if r.get("request_id")!=receipt:e.append(f"{name}: receipt id mismatch")
   if name.endswith("timeout") and r.get("stop_reason")!="HOST_BROKER_SUBPROCESS_TIMEOUT":e.append("timeout not typed")
   if name.endswith("unavailable") and r.get("stop_reason")!="HOST_BROKER_EXECUTABLE_UNAVAILABLE":e.append("unavailable not typed")
   want=0 if name in ("baseline_exit0","candidate_exit0","candidate_two_queued") else 7 if name.endswith("exit7") else None
   if r.get("returncode")!=want:e.append(f"{name}: returncode mismatch")
  except Exception as x:e.append(f"{name}: receipt absent/unreadable: {x}")
 if (OUT/"candidate_malformed"/"bad.broker.json").exists():e.append("malformed request produced broker receipt")
 if (OUT/"candidate_malformed"/"bad.response.jsonl").exists():e.append("malformed request produced response")
 try:
  names=sorted(p.name for p in (OUT/"candidate_two_queued").glob("*.broker.json"))
  if names!=["r1.broker.json"]:e.append(f"one-shot receipt cardinality: {names}")
  responses=sorted(p.name for p in (OUT/"candidate_two_queued").glob("*.response.jsonl"))
  if responses!=["r1.response.jsonl"]:e.append(f"one-shot response cardinality: {responses}")
 except Exception as x:e.append(f"one-shot audit failure: {x}")
 s=load(OUT/"runner_summary.json")
 if s.get("fake_invocations")!=5:e.append(f"fake invocation count {s.get('fake_invocations')} != 5")
 if not s.get("malformed_no_fake_invocation"):e.append("malformed request invoked fake executable")
 return e
def main():
 es=errors(); result={"audit":"PASS_BROKER_EXIT_CONTRACT" if not es else "FAIL_BROKER_EXIT_CONTRACT","errors":es}
 (OUT/"audit_result.json").write_text(json.dumps(result,indent=2)+"\n"); print(json.dumps(result,sort_keys=True)); raise SystemExit(bool(es))
if __name__=="__main__":main()
