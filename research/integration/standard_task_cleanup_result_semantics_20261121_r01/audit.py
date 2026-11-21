from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parent
REPO=Path(subprocess.check_output(["git","rev-parse","--show-toplevel"],cwd=ROOT,text=True).strip())
EXCLUDED={"SHA256SUMS","audit.json","audit.exit-code.txt","audit.py"}
def sha(path):
 data=path.read_bytes()
 if path.suffix.lower() not in {".png",".jpg",".jpeg",".bin"}: data=data.replace(b"\r\n",b"\n")
 return hashlib.sha256(data).hexdigest()
def main():
 c=json.loads((ROOT/"conditions.json").read_text(encoding="utf-8")); revision=c["source_revision"]
 checked=0
 for row in (ROOT/"source-blobs.txt").read_text(encoding="ascii").splitlines():
  expected,path=row.split("  ",1); actual=subprocess.check_output(["git","rev-parse",f"{revision}:{path}"],cwd=REPO,text=True).strip()
  if actual!=expected: raise SystemExit(f"source pin mismatch: {path}")
  checked+=1
 out=json.loads((ROOT/"observed-output.json").read_text(encoding="utf-8"))
 assert out["status"]=="cleanup_failed" and out["program_completed"] is True and out["task_success"] is False
 assert out["raw_dispatch"]["result"]["task_success"] is True
 assert "release readback failed"==out["cleanup_error"]
 for name in ("test-normal.log","test-optimized.log"):
  if "Ran 13 tests" not in (ROOT/name).read_text(encoding="utf-8") or "OK" not in (ROOT/name).read_text(encoding="utf-8"): raise SystemExit(f"test record missing pass: {name}")
 manifest={}
 for row in (ROOT/"SHA256SUMS").read_text(encoding="ascii").splitlines():
  digest,path=row.split("  ",1); manifest[path]=digest
 actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p.relative_to(ROOT).as_posix() not in EXCLUDED and "__pycache__" not in p.parts and p.suffix!=".pyc"}
 if actual!=set(manifest): raise SystemExit("manifest file set mismatch")
 for path,digest in manifest.items():
  if sha(ROOT/path)!=digest: raise SystemExit(f"checksum mismatch: {path}")
 result={"status":"PASS_AUDIT_CLEANUP_AND_TASK_ASSERTIONS_PRESERVED","source_revision":revision,"source_blobs_checked":checked,"manifest_files_verified":len(manifest),"normal_tests":"13/13 PASS","optimized_tests":"13/13 PASS","top_level_task_success":False,"raw_task_success":True,"qualified_status":"cleanup_failed"}
 (ROOT/"audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 (ROOT/"audit.exit-code.txt").write_text("0\n",encoding="ascii")
 print(json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
