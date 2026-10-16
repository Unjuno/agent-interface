import json, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
SOURCE=ROOT / "research/doom/results/map01-v39-release-cleanup-owner-queue-composition-v1"
FILES=["README.md","RUN.json","SOURCE_MANIFEST.json","audit.py","composition_test.py","research/doom/doom_typed_release_backend_v3.py","research/doom/doom_typed_release_backend_v3_parent.py","research/live_control/input_owner_v10.py","research/live_control/input_transition_owner_v3.py","results/RAW_COMPOSITION.txt","results/composition.json"]
MUTATIONS={
 "candidate_cancel_claim": lambda d: next(o for o in d["observations"] if o["candidate"] and o["cause"]=="cancelled").update(ordinary_release_candidate=True),
 "candidate_expiry_order": lambda d: next(o for o in d["observations"] if o["candidate"] and o["cause"]=="expired").update(owner_release_verified_ns=999999999999999999),
 "parent_false_positive": lambda d: next(o for o in d["observations"] if not o["candidate"] and o["cause"]=="expired").update(owner_transition_verified=False),
 "xlib_event_count": lambda d: d["observations"][0].update(xlib_event_count=3),
}
def main():
 checks=[]
 with tempfile.TemporaryDirectory(prefix="map01-v39-audit-mut-") as tmp:
  root=Path(tmp)/"base"; root.mkdir()
  for rel in FILES:
   p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(SOURCE/rel,p)
  cases=[("baseline",None,False), *((name,mut,True) for name,mut in MUTATIONS.items())]
  for name,mut,expected_reject in cases:
   case=Path(tmp)/name
   if name=="baseline": case=root
   else:
    shutil.copytree(root,case)
    p=case/"results/composition.json"; data=json.loads(p.read_text(encoding="utf-8")); mut(data); p.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
   r=subprocess.run([sys.executable,"-B","audit.py"],cwd=case,text=True,capture_output=True)
   rejected=r.returncode!=0
   checks.append({"case":name,"expected_reject":expected_reject,"exit_code":r.returncode,"rejected":rejected})
   print(f"{name}: expected_reject={expected_reject} rejected={rejected} exit={r.returncode}")
  passed=all(c["rejected"]==c["expected_reject"] for c in checks)
  print("PASS_AUDIT_MUTATIONS" if passed else "FAIL_AUDIT_MUTATIONS")
  return 0 if passed else 1
if __name__=="__main__": raise SystemExit(main())
