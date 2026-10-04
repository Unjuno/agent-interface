from pathlib import Path, PurePosixPath
import hashlib, json, subprocess, sys

PKG = Path(__file__).resolve().parent
REPO = PKG.parents[3]
PREFIX = "research/doom/results/v39_adapter_edge_cardinality_59_a01_20261005"
checks=[]
def ck(ok, label): checks.append((bool(ok), label))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(rel): return json.loads((PKG/rel).read_text(encoding="utf-8-sig"))

def excluded(rel):
    parts=PurePosixPath(rel).parts
    return "__pycache__" in parts or rel.lower().endswith(".pyc")

# Frozen A01 source, fixture, scripts, result, and independently reconstructed audit.
f=load("FREEZE.json")
a2=load("AUDIT_V2_FREEZE.json")
ck(sha(PKG/"src/map01_overlap_controller_v39.py")==f["source"]["controller_sha256"],"A01 controller SHA256")
ck(sha(PKG/"src/candidate-events.jsonl")==f["input"]["sha256"],"A01 fixture SHA256")
ck(sha(PKG/"src/candidate.py")==f["candidate"]["sha256"],"A01 candidate script SHA256")
ck(sha(PKG/"src/audit.py")==f["independent_auditor"]["sha256"],"A01 preliminary auditor SHA256")
ck(sha(PKG/"raw/candidate.json")==a2["inputs"]["candidate_sha256"],"A01 frozen candidate result SHA256")
ck(sha(PKG/"audit-v2-src/audit.py")==a2["auditor"]["sha256"],"A01 audit-v2 script SHA256")
candidate=load("raw/candidate.json")
ck(candidate["experiment"]==f["experiment_id"],"A01 experiment identity")
ck(candidate["source_commit"]==f["source"]["parent_head"],"A01 source commit identity")
ck(candidate["fixture_sha256"]==f["input"]["sha256"],"A01 candidate fixture identity")
audit=load("audit-v2/audit.json")
ck(audit["audit"]=="PASS" and audit["checks"]==66 and not audit["errors"],"A01 independent raw-derived audit-v2")
ck(audit["candidate_sha256"]==a2["inputs"]["candidate_sha256"],"A01 audit-v2 candidate binding")
ck(audit["source_sha256"]==a2["inputs"]["source_sha256"],"A01 audit-v2 source binding")
ck(audit["fixture_sha256"]==a2["inputs"]["fixture_sha256"],"A01 audit-v2 fixture binding")
ck(audit["tamper_control"]=="PASS","A01 coherent corruption control")

# Current-head A02B pins the actual bytes used by the isolated run.
b=load("AUDIT_A02B_FREEZE.json")
br=load("AUDIT_A02B_RESULT.json")
source=PKG/b["source_snapshots"]["controller"]
test=PKG/b["source_snapshots"]["test"]
runner=PKG/b["runner"]["path"]
ck(b["status"]=="FROZEN_BEFORE_RUN","A02B preregistration status")
ck(b["base_pr_head"]=="a7f9e9e3c4bd31199bde3a14761783ead619ad08","A02B current parent identity")
ck(sha(source)==b["source"]["sha256"],"A02B controller snapshot SHA256")
ck(sha(test)==b["test"]["sha256"],"A02B exact proposed test snapshot SHA256")
a06_path=REPO/"research/doom/v39_adapter_nested_identity_taint_59_a06_20261005/A06_RESULT.json"
a06=json.loads(a06_path.read_text(encoding="utf-8"))
ck(sha(REPO/"research/doom/test_map01_v39_typed_state_feedback.py")==a06["test_sha256"],"A06 live branch test SHA256")
ck(sha(REPO/"research/doom/map01_overlap_controller_v39.py")==a06["candidate_source_sha256"],"A06 live branch controller SHA256")
ck(sha(runner)==b["runner"]["sha256"],"A02B runner SHA256")
for snapshot,key in ((source,"source"),(test,"test")):
    blob=subprocess.check_output(["git","-C",str(REPO),"hash-object","--no-filters",str(snapshot)],text=True).strip()
    ck(blob==b[key]["git_blob"],"A02B "+key+" Git blob identity")
result_path=PKG/br["result_path"]
result=load(br["result_path"])
ck(sha(result_path)==br["result_sha256"],"A02B result SHA256")
ck(sha(PKG/br["container_log_path"])==br["container_log_sha256"],"A02B captured container log SHA256")
ck(br["status"]=="PASS_HASH_PINNED_SOURCE_EXTRACTED_TEST" and br["container_exit_code"]==0 and br["container_count"]==1,"A02B accepted container outcome")
ck(result["result"]=="PASS" and result["unittest_methods"]==1 and result["duplicate_subcases"]==5,"A02B test result")
ck(result["controller_sha256"]==b["source"]["sha256"] and result["test_sha256"]==b["test"]["sha256"],"A02B output source/test bindings")
ck(result["py_compile"]=="PASS","A02B byte-compilation result")
ck(result["resource_snapshot"]["cpu_max"]=="100000 100000" and result["resource_snapshot"]["memory_max"]=="536870912","A02B observed CPU/memory cgroups")
ck(result["resource_snapshot"]["memory_swap_max"]=="max","A02B swap limitation recorded")
post=load("raw/a02b-postflight-list-capture.json")
ck(post["returncode"]==0 and post["stdout"]=="" and post["stderr"]=="","A02B post-run list capture preserved verbatim")
gap=load("raw/a02b-preflight-capture-gap.json")
ck(gap["status"]=="CAPTURE_GAP" and gap["command_was_invoked_before_run"] and "No claim" in gap["observation"],"A02B missing preflight is explicit")

# Historical A02 files are explicitly reconstructed and are not counted as accepted evidence.
h=load("historical-a02-reconstructed/FREEZE_RECONSTRUCTED.json")
history_test=PKG/"historical-a02-reconstructed/test-bytes-recorded-by-prior-freeze.py"
ck(h["provenance_status"]=="RECONSTRUCTED_NOT_ACCEPTED_AS_RAW_AUDIT_EVIDENCE","historical A02 downgraded provenance")
ck(sha(history_test)=="bdd7092901ab6faad926a86333848b4a5c51d23b0a43aa51537f6974f66b571d","historical test bytes recovered exactly")
ck(not (PKG/"historical-a02-reconstructed/runner-corrected-7b835.py").exists(),"historical corrected runner not falsely represented as recovered")

# Manifest paths are relative, unique, contained, and equal the complete indexed package set.
manifest_path=PKG/"SHA256SUMS"
lines=manifest_path.read_text(encoding="utf-8-sig").splitlines()
entries={}
valid=True
for line in lines:
    if "  " not in line:
        valid=False; continue
    digest,rel=line.split("  ",1)
    pp=PurePosixPath(rel)
    if (not rel or pp.is_absolute() or ".." in pp.parts or "\\" in rel or
        len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest) or
        rel=="SHA256SUMS" or excluded(rel)):
        valid=False; continue
    if rel in entries:
        valid=False; continue
    full=(PKG/Path(*pp.parts)).resolve()
    if not full.is_relative_to(PKG.resolve()) or not full.is_file():
        valid=False; continue
    entries[rel]=digest
ck(valid,"manifest syntax, safe paths, and unique entries")
for rel,digest in entries.items(): ck(sha(PKG/Path(*PurePosixPath(rel).parts))==digest,"manifest hash "+rel)
index_raw=subprocess.check_output(["git","-C",str(REPO),"ls-files","--cached","-z","--",PREFIX])
tracked={x.decode("utf-8").removeprefix(PREFIX+"/") for x in index_raw.split(b"\0") if x}
tracked={x for x in tracked if not excluded(x)}
tracked.discard("SHA256SUMS")
ck(set(entries)==tracked,"manifest exactly matches indexed package files except itself")
on_disk={x.relative_to(PKG).as_posix() for x in PKG.rglob("*") if x.is_file() and not excluded(x.relative_to(PKG).as_posix())}
on_disk.discard("SHA256SUMS")
ck(on_disk==tracked,"on-disk package files match indexed files; caches/pyc excluded deterministically")
failed=[label for ok,label in checks if not ok]
print(json.dumps({"audit":"PASS" if not failed else "FAIL","checks":len(checks),"manifest_entries":len(entries),"errors":failed},indent=2))
raise SystemExit(0 if not failed else 1)
