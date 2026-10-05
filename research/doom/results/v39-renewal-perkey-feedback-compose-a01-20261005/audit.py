#!/usr/bin/env python3
import hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
PKG=Path(__file__).resolve().parent
f=json.loads((PKG/"FREEZE.json").read_text(encoding="utf-8"))
base=f["base_main_commit"]
checks={
 "base_commit_exists":subprocess.run(["git","cat-file","-e",base],cwd=ROOT).returncode==0,
 "base_is_ancestor":subprocess.run(["git","merge-base","--is-ancestor",base,"HEAD"],cwd=ROOT).returncode==0,
 "base_v39_blob_matches":subprocess.run(["git","rev-parse",f"{base}:research/doom/map01_overlap_controller_v39.py"],cwd=ROOT,text=True,capture_output=True).stdout.strip()==f["base_main_v39_controller_blob"],
}
for group in ("sources","tests"):
 for name,digest in f[group].items():
  checks[f"{group}:{name}"]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
result={"schema":"issue59-v39-renewal-perkey-feedback-compose-a01-audit","checks":checks,"pass":all(checks.values())}
(PKG/"AUDIT.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if result["pass"] else 1)
