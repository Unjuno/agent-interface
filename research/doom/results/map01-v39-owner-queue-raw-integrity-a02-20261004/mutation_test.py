import hashlib, json, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
SOURCE=ROOT / "research/doom/results/map01-v39-release-cleanup-owner-queue-composition-v1"
def verify_manifest(root):
 sums=root/"SHA256SUMS.txt"; failures=[]; checks=0
 for line in sums.read_text(encoding="utf-8").splitlines():
  digest, rel=line.split("  ",1); path=(root/rel).resolve()
  if root.resolve() not in path.parents: failures.append({"path":rel,"error":"path_escape"}); continue
  if not path.is_file(): failures.append({"path":rel,"error":"missing"}); continue
  checks+=1; actual=hashlib.sha256(path.read_bytes()).hexdigest()
  if actual!=digest: failures.append({"path":rel,"error":"sha256_mismatch","expected":digest,"actual":actual})
 return {"checks":checks,"failures":failures,"pass":not failures}
def run_audit(root):
 r=subprocess.run([sys.executable,"-B","audit.py"],cwd=root,text=True,capture_output=True)
 return {"exit_code":r.returncode,"stdout":r.stdout,"stderr":r.stderr}
def main():
 with tempfile.TemporaryDirectory(prefix="map01-v39-raw-integrity-") as td:
  base=Path(td)/"baseline"; shutil.copytree(SOURCE,base)
  before=verify_manifest(base); baseline=run_audit(base); baseline_after=verify_manifest(base)
  corrupt=Path(td)/"contradictory-raw"; shutil.copytree(SOURCE,corrupt)
  raw=corrupt/"results/RAW_COMPOSITION.txt"; raw.write_text(raw.read_text(encoding="utf-8")+"\nFAIL: injected contradictory raw runner outcome\n",encoding="utf-8")
  changed=verify_manifest(corrupt); old_audit=run_audit(corrupt)
  result={"schema":"map01-v39-owner-queue-raw-integrity-a02-v1","hypothesis":"The saved-result auditor's substring check does not reject contradictory raw runner text, while the existing SHA256SUMS manifest identifies the changed bytes.","parent_commit":"23290e22615e9f9d4f10b6ab4694429e19757c9a","baseline_manifest":before,"baseline_audit_exit":baseline["exit_code"],"baseline_manifest_after_audit":baseline_after,"mutated_manifest":changed,"mutated_audit_exit":old_audit["exit_code"],"mutated_audit_passed":"PASS_OWNER_QUEUE_COMPOSITION" in old_audit["stdout"],"pass":before["pass"] and baseline["exit_code"]==0 and baseline_after["pass"] and not changed["pass"] and old_audit["exit_code"]==0 and "PASS_OWNER_QUEUE_COMPOSITION" in old_audit["stdout"],"scope":"saved fake-Xlib evidence integrity only; no live input or allocation"}
  output=Path(__file__).resolve().parent
  (output/"results.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
  lines=["baseline_manifest_pass="+str(before["pass"]),"baseline_audit_exit="+str(baseline["exit_code"]),"baseline_manifest_after_audit_pass="+str(baseline_after["pass"]),"mutated_manifest_pass="+str(changed["pass"]),"mutated_manifest_failures="+str(len(changed["failures"])),"mutated_old_audit_exit="+str(old_audit["exit_code"]),"mutated_old_audit_passed="+str("PASS_OWNER_QUEUE_COMPOSITION" in old_audit["stdout"]),"PASS_RAW_INTEGRITY_COUNTEREXAMPLE" if result["pass"] else "FAIL_RAW_INTEGRITY_COUNTEREXAMPLE"]
  (output/"RAW_INTEGRITY.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
  print("\n".join(lines))
  return 0 if result["pass"] else 1
if __name__=="__main__": raise SystemExit(main())
