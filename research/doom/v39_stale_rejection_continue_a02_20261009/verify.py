"""Recheck A02 source identity, raw mutation outcomes, and package hashes."""
import hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
f=json.loads((ROOT/"FREEZE.json").read_text())
errors=[]
def git(*args): return subprocess.check_output(["git",*args],cwd=REPO)
src=git("show",f"{f['tested_pr_head_before_addition']}:{f['source']['path']}")
for key,data in (("source",src),("test",(REPO/f["test"]["path"]).read_bytes())):
 item=f[key]
 if hashlib.sha256(data).hexdigest()!=item["sha256"] or len(data)!=item["bytes"]: errors.append(key+" sha/size mismatch")
 if key=="source" and git("rev-parse",f"{f['tested_pr_head_before_addition']}:{item['path']}").decode().strip()!=item["git_blob"]: errors.append("controller git blob mismatch")
 if key=="test" and git("hash-object","--",item["path"]).decode().strip()!=item["git_blob"]: errors.append("test git blob mismatch")
message="stale rejection must skip normal completion and continue the outer iteration"
for name,item in f["runs"].items():
 code=(ROOT/"results"/(name+".exit")).read_text().strip(); output=(ROOT/"results"/(name+".stdout.txt")).read_text()+(ROOT/"results"/(name+".stderr.txt")).read_text(); bad=name.startswith("mutation")
 if bad and (code=="0" or not item["assertion_observed"] or message not in output): errors.append(name+" did not reject mutation at target assertion")
 if not bad and (code!="0" or "Ran 1 test" not in output or "OK" not in output): errors.append(name+" positive run failed")
manifest=ROOT/"SHA256SUMS.txt"; expected={}
for line in manifest.read_text().splitlines():
 digest,path=line.split("  ",1); expected[path]=digest
actual={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob("*") if p.is_file() and p!=manifest}
if expected!=actual: errors.append("SHA256SUMS mismatch")
if errors: raise SystemExit("FAIL\n"+"\n".join(errors))
print(json.dumps({"audit":"PASS_V39_STALE_REJECTION_CONTINUE_A02","source_head":f["tested_pr_head_before_addition"],"raw_runs_checked":len(f["runs"]),"scope":f["scope"]},indent=2))
