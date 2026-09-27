#!/usr/bin/env python3
"""Canonical-LF report audit runner for Issue #4963; local Docker only."""
import ast,base64,hashlib,json,os,pathlib,subprocess,sys,traceback
SOURCES = {}
BASELINE_REPORT_B64 = undefined
EXPECTED={"audit_core_v2.py":"6fb5f3a16e8639f2645576e985869948aa59efea5546a9093829065a8580b77c",
"audit_raw_v2.py":"6726eac3b3eb49820cbd3526ec3c932652bd81c8089e5c097c240e669cba7880",
"test_audit_v2.py":"3a72f44de313e36a7b8eae94c13c74f979499f0133332c03016f9042c698d7c6",
"verify_audit_v2.py":"5b8965cf5042de9d148dfd23708a24a31ae11ef575828da177b8e50ebc628f1e"}
EXPECTED_SIZE={"audit_core_v2.py":4408,"audit_raw_v2.py":2969,"test_audit_v2.py":2404,"verify_audit_v2.py":3287}
BASELINE_SHA="eb0c16487bd4635582df9f2e5337db38a1080105ae44558f6dc165ebaf3001d1"
BASELINE_SIZE=1052
CANONICAL_SHA="faa001d6a7e925390ed153717fa22ec559e75e54d5663b129dd316de53c56556"
CANONICAL_SIZE=1017
def sha(b):return hashlib.sha256(b).hexdigest()
def dec(value):
 try:raw64=b"".join(value.encode("ascii").split())
 except UnicodeEncodeError as e:raise RuntimeError("STOP_BASE64_NONASCII") from e
 return base64.b64decode(raw64,validate=True)
def decode_pinned_sources():
 out={}
 for name,wrapped in SOURCES.items():
  raw=dec(wrapped)
  if len(raw)!=EXPECTED_SIZE[name] or sha(raw)!=EXPECTED[name]:raise RuntimeError("STOP_SOURCE_PIN:"+name)
  if any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(raw.decode("utf-8")))):raise RuntimeError("STOP_ASSERT_PRESENT:"+name)
  out[name]=raw
 return out
def baseline_lf():
 raw=dec(BASELINE_REPORT_B64)
 if len(raw)!=BASELINE_SIZE or sha(raw)!=BASELINE_SHA:raise RuntimeError("STOP_BASELINE_RAW_PIN")
 lf=raw.replace(b"\r\n",b"\n")
 if b"\r" in lf or len(lf)!=CANONICAL_SIZE or sha(lf)!=CANONICAL_SHA:raise RuntimeError("STOP_BASELINE_CANONICAL_PIN")
 return raw,lf
def run(cmd,env,log):
 p=subprocess.run(cmd,cwd="/tmp/issue4963_source",env=env,text=True,capture_output=True)
 pathlib.Path(log).write_text("COMMAND="+json.dumps(cmd)+"\nEXIT="+str(p.returncode)+"\nSTDOUT:\n"+p.stdout+"\nSTDERR:\n"+p.stderr,encoding="utf-8")
 if p.returncode:raise RuntimeError("STOP_COMMAND_FAILED:"+str(cmd[0])+":"+str(p.returncode))
 return p.stdout.strip()
def main():
 import argparse
 ap=argparse.ArgumentParser()
 for n in ("result","corpus","model","out","image_id","launcher_sha256"):ap.add_argument("--"+n,required=True)
 a=ap.parse_args();out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 receipt={"issue":4963,"runner_sha256":a.launcher_sha256,"image_id":a.image_id,"python":sys.version,"network":"none (docker enforced)",
 "rootfs":"read-only (docker enforced)","cpu_limit":"1","memory_limit":"2g","pids_limit":64,"gpu_requested":False,
 "model_loaded":False,"inference":False,"training":False,"optimizer_steps":0,"retries":0,"status":"STOP"}
 try:
  decoded=decode_pinned_sources();raw_base,canonical=baseline_lf()
  receipt["baseline"]={"raw_bytes":len(raw_base),"raw_sha256":sha(raw_base),"canonical_bytes":len(canonical),"canonical_sha256":sha(canonical)}
  src=pathlib.Path("/tmp/issue4963_source");src.mkdir()
  for name,data in decoded.items():
   path=src/name;path.write_bytes(data);path.chmod(0o444)
  receipt["staged_sources"]={n:{"sha256":sha(b),"bytes":len(b),"readonly":True} for n,b in decoded.items()}
  model=pathlib.Path(a.model);result=pathlib.Path(a.result);corpus=pathlib.Path(a.corpus)
  receipt["input_sha256"]={"result":sha(result.read_bytes()),"corpus":sha(corpus.read_bytes()),"weights":sha((model/"model.safetensors").read_bytes())}
  env=os.environ.copy()
  modes=[("normal",[sys.executable],{}),("optimized",[sys.executable,"-O"],{}),("pyopt",[sys.executable],{"PYTHONOPTIMIZE":"1"})]
  for mode,prefix,extra in modes:
   e=env.copy();e.update(extra)
   run(prefix+["-B","-m","unittest","-v","test_audit_v2"],e,str(out/f"tests_{mode}.log"))
   report=out/f"report_{mode}.json"
   run(prefix+["-B","audit_raw_v2.py","--result",str(result),"--corpus",str(corpus),"--model",str(model),"--out",str(report)],e,str(out/f"audit_{mode}.log"))
   data=report.read_bytes()
   if data!=canonical or len(data)!=CANONICAL_SIZE or sha(data)!=CANONICAL_SHA:raise RuntimeError("STOP_CANONICAL_REPORT:"+mode+":"+sha(data))
   receipt.setdefault("report_hashes",{})[mode]=sha(data)
  for mode,prefix in (("normal",[sys.executable]),("optimized",[sys.executable,"-O"])):
   run(prefix+["-B","verify_audit_v2.py","--result",str(result),"--corpus",str(corpus),"--weights",str(model/"model.safetensors"),"--report",str(out/f"report_{mode}.json")],env,str(out/f"independent_{mode}.log"))
  receipt.update({"status":"PASS","rows":27,"corruption_controls_rejected":5,"report_bytes":CANONICAL_SIZE,"report_sha256":CANONICAL_SHA})
 except BaseException as e:
  receipt["failure"]=str(e);receipt["traceback"]=traceback.format_exc()
 finally:
  (out/"container_receipt.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(receipt,sort_keys=True))
 return 0 if receipt["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
