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
 c=json.loads((ROOT/"conditions.json").read_text(encoding="utf-8")); rev=c["source_revision"]; current=c["current_main_revision"]; head=subprocess.check_output(["git","rev-parse","origin/main"],cwd=REPO,text=True).strip()
 subprocess.check_call(["git","merge-base","--is-ancestor",current,head],cwd=REPO,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 checked=0
 for row in (ROOT/"source-blobs.txt").read_text(encoding="ascii").splitlines():
  expected,path=row.split("  ",1); actual=subprocess.check_output(["git","rev-parse",f"{rev}:{path}"],cwd=REPO,text=True).strip()
  if actual!=expected: raise SystemExit(f"source pin mismatch: {path}")
  current_blob=subprocess.check_output(["git","rev-parse",f"{current}:{path}"],cwd=REPO,text=True).strip()
  if current_blob!=expected: raise SystemExit(f"recorded current-main source drift: {path}")
  head_blob=subprocess.check_output(["git","rev-parse",f"{head}:{path}"],cwd=REPO,text=True).strip()
  if head_blob!=expected: raise SystemExit(f"origin/main source drift: {path}")
  if hashlib.sha256((REPO/path).read_bytes()).hexdigest()!=c["sha256"][path]: raise SystemExit(f"materialized fixture hash mismatch: {path}")
  checked+=1
 r1=ROOT/"r01_sparse_failure"
 for mode in ("normal","optimized"):
  text=(r1/f"{mode}.log").read_text(encoding="utf-8",errors="replace")
  if "FileNotFoundError" not in text or "first.fods" not in text: raise SystemExit(f"R01 {mode} sparse failure missing")
 r2=ROOT/"r02_materialized_archive"
 for mode in ("normal","optimized"):
  text=(r2/f"{mode}.log").read_text(encoding="utf-8",errors="replace")
  code=int((r2/f"{mode}.exit-code.txt").read_text(encoding="ascii").strip())
  if code!=0 or "Ran 3 tests" not in text or "OK" not in text: raise SystemExit(f"R02 {mode} not a clean 3/3 pass")
  ledger=json.loads((r2/f"{mode}.attempt-ledger.json").read_text(encoding="utf-8"))
  if ledger.get("evidence_class")!="fake_x_process_stdio_fixture": raise SystemExit(f"{mode}: fixture class missing")
  if ledger.get("provider_usage_status")!="unknown_unobserved_by_fixture" or ledger.get("provider_usage") is not None: raise SystemExit(f"{mode}: provider usage overstated")
  if ledger.get("task_success") is not True or ledger.get("replay_allowed") is not False: raise SystemExit(f"{mode}: task/replay result mismatch")
  if ledger.get("input_release_verified") is not True or ledger.get("owner_close_status")!="closed": raise SystemExit(f"{mode}: release/close receipt missing")
  task=ledger.get("task_effect",{})
  if task.get("profile_id")!="calc-g10-two-save-v1" or task.get("status")!="verified": raise SystemExit(f"{mode}: G10 profile/effect missing")
  saved=task.get("saved_effects",{})
  if set(saved)!={"first","second"} or any(saved[k].get("effect",{}).get("effect_match") is not True for k in saved): raise SystemExit(f"{mode}: two saved-byte effects not verified")
  calls={row.get("tool"):row for row in ledger.get("mcp_calls",[])}
  if "interface_guarded_calc_compiled" not in calls or calls.get("interface_verify_task",{}).get("status")!="verified": raise SystemExit(f"{mode}: public MCP caller/scorer receipts missing")
 manifest={}
 for row in (ROOT/"SHA256SUMS").read_text(encoding="ascii").splitlines():
  digest,path=row.split("  ",1); manifest[path]=digest
 actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p.relative_to(ROOT).as_posix() not in EXCLUDED and "__pycache__" not in p.parts and p.suffix!=".pyc"}
 if actual!=set(manifest): raise SystemExit("manifest file-set mismatch")
 for path,digest in manifest.items():
  if sha(ROOT/path)!=digest: raise SystemExit(f"checksum mismatch: {path}")
 audit={"status":"PASS_AUDIT_G10_CURRENT_MAIN_STDIO_R02","source_revision":rev,"current_main_revision_at_record":current,"origin_main_revision_at_audit":head,"source_blobs_checked":checked,"manifest_files_verified":len(manifest),"r01":"HOLD_SPARSE_ARCHIVE_MISSING; failure retained, exit code unavailable","r02_normal":"PASS_3_OF_3_EXIT_0","r02_optimized":"PASS_3_OF_3_EXIT_0","r02_both_saved_fixture_effects_verified":True,"r02_input_release_verified":True,"r02_owner_close":"closed","provider_usage":"unknown_unobserved_by_fixture","limits":c["limits"]}
 (ROOT/"audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 (ROOT/"audit.exit-code.txt").write_text("0\n",encoding="ascii")
 print(json.dumps(audit,sort_keys=True))
if __name__=="__main__": main()
