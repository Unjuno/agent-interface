#!/usr/bin/env python3
"""One-shot Tesseract extraction over 20 frozen epoch-8 A04 crops only."""
import base64,hashlib,json,pathlib,platform,subprocess,sys
PKG=pathlib.Path(__file__).resolve().parent; ROOT=PKG.parents[2]
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
 f=json.loads((PKG/"FREEZE.json").read_text()); tess=f["tesseract_path"]
 if (pathlib.Path(sys.executable).resolve().as_posix()!=f["python_executable"] or sys.version!=f["python_version"] or platform.platform()!=f["platform"] or platform.machine()!=f["machine"] or platform.release()!=f["kernel_release"]): raise SystemExit("frozen host/Python identity mismatch")
 if sha((PKG/"FREEZE.json").read_bytes())!=(PKG/"FREEZE.sha256").read_text().split()[0]: raise SystemExit("freeze sidecar mismatch")
 for rel,h in f["inputs"].items():
  if sha((ROOT/rel).read_bytes())!=h: raise SystemExit("frozen input mismatch: "+rel)
 for rel,h in f["code_sources"].items():
  if sha((PKG/rel).read_bytes())!=h: raise SystemExit("frozen code mismatch: "+rel)
 version=subprocess.run([tess,"--version"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if version.returncode or version.stdout.decode("utf-8","replace").splitlines()[0]!=f["tesseract_version"]: raise SystemExit("Tesseract version mismatch")
 if sha(pathlib.Path(tess).read_bytes())!=f["tesseract_sha256"] or sha(pathlib.Path(f["eng_traineddata_path"]).read_bytes())!=f["eng_traineddata_sha256"]: raise SystemExit("Tesseract identity mismatch")
 a04=json.loads((ROOT/f["a04_candidate_path"]).read_text()); rows=[r for r in a04["rows"] if r["frame_id"]==f["frame_id"] and r["selected_kind"]=="FOCUSED_REGION"]
 if len(rows)!=20: raise SystemExit(f"expected 20 fixed crops, got {len(rows)}")
 output=[]
 for row in rows:
  rel=f["a04_package"]+"/"+row["focus_png_path"]; data=(ROOT/rel).read_bytes()
  proc=subprocess.run([tess,"stdin","stdout","--psm",str(f["psm"]),"-l","eng","--tessdata-dir",f["tessdata_dir"]],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  text=proc.stdout.decode("utf-8","replace")
  output.append({"case_id":row["case_id"],"png_path":rel,"bounds":row["request"]["bounds"],"payload_bytes":row["focus_payload_bytes"],"full_payload_bytes":row["full_payload_bytes"],"input_sha256":sha(data),"ocr_exit":proc.returncode,"ocr_stdout_b64":base64.b64encode(proc.stdout).decode("ascii"),"ocr_stdout_sha256":sha(proc.stdout),"ocr_text":text,"ocr_stderr_b64":base64.b64encode(proc.stderr).decode("ascii"),"ocr_stderr_sha256":sha(proc.stderr),"ocr_stderr":proc.stderr.decode("utf-8","replace")})
 raw={"schema":"a09-ocr-output-v1","freeze_sha256":sha((PKG/"FREEZE.json").read_bytes()),"pilot_stdout_sha256":f["pilot_stdout_sha256"],"case_count":len(output),"rows":output}
 sys.stdout.write(json.dumps(raw,sort_keys=True,separators=(",",":"))+"\n")
 return 0 if all(r["ocr_exit"]==0 for r in output) else 1
if __name__=="__main__": raise SystemExit(main())
