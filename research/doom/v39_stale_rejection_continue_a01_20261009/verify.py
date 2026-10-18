"""Independent source, output, mutation, and package-integrity audit."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
freeze=json.loads((ROOT/"FREEZE.json").read_text(encoding="utf-8"))
result=json.loads((ROOT/"RESULT.json").read_text(encoding="utf-8"))
failures=[]
for rel,identity in freeze["source_files"].items():
    data=subprocess.check_output(["git","show",f"{freeze['source_main_commit']}:{rel}"]) if rel != freeze["test_path"] else (REPO/rel).read_bytes()
    sha=hashlib.sha256(data).hexdigest()
    if sha != identity["sha256"] or len(data) != identity["bytes"]:
        failures.append(f"source sha/size mismatch: {rel}")
    if rel != freeze["test_path"]:
        oid=subprocess.check_output(["git","rev-parse",f"{freeze['source_main_commit']}:{rel}"],text=True).strip()
    else:
        oid=subprocess.check_output(["git","hash-object","--",str(REPO/rel)],cwd=REPO,text=True).strip()
    if oid != identity["git_blob"]:
        failures.append(f"source blob mismatch: {rel}")

message=result["mutation_assertion_message"]
for key in ("pass-normal","pass-optimized","mutation-normal","mutation-optimized"):
    output=(ROOT/"results"/f"{key}.stdout.txt").read_text(encoding="utf-8")+(ROOT/"results"/f"{key}.stderr.txt").read_text(encoding="utf-8")
    code=(ROOT/"results"/f"{key}.exit").read_text(encoding="ascii").strip()
    if key.startswith("pass-"):
        if code != "0" or "Ran 1 test" not in output or "OK" not in output:
            failures.append(f"positive run invalid: {key}")
    else:
        if code == "0" or "FAIL" not in output or message not in output:
            failures.append(f"mutation did not fail at target assertion: {key}")
if result["status"] != "PASS_TESTED_CONTROL_FLOW_WITH_EXPECTED_MUTATION_REJECTION":
    failures.append("unexpected result status")
manifest=ROOT/"SHA256SUMS.txt"
expected={}
for line in manifest.read_text(encoding="utf-8").splitlines():
    digest,rel=line.split("  ",1);expected[rel]=digest
actual={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob("*") if p.is_file() and p != manifest}
if expected != actual:failures.append("package checksum manifest mismatch")
if failures:raise SystemExit("AUDIT_FAIL\n"+"\n".join(failures))
print(json.dumps({"audit":"PASS_STALE_REJECTION_CONTINUE_MUTATION","source_files_checked":len(freeze["source_files"]),"runs_checked":4,"scope":"static control-flow regression only"},indent=2))
