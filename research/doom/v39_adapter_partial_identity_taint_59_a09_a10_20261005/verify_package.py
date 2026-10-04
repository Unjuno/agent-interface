from pathlib import Path,PurePosixPath
import hashlib,json,sys
H=Path(__file__).resolve().parent;D=H.parent;REPO=D.parents[1];checks=[]
def ck(v,n):checks.append((bool(v),n))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((H/n).read_text(encoding="utf-8-sig"))
final=load("FINAL_VALIDATION.json");freeze9=load("A09_FREEZE.json");freeze10=load("A10_FREEZE.json");freeze11=load("A11_FREEZE.json");replay=load("REPLAY_RESULT.json");audit=load("REPLAY_AUDIT.json");a11=load("A11_RESULT.json");a11audit=load("A11_AUDIT.json");integration=load("PR_BASE_INTEGRATION.json")
ck(sha(REPO/"research/doom/map01_overlap_controller_v39.py")==final["candidate_source_sha256"],"current controller pin")
ck(sha(REPO/"research/doom/test_map01_v39_typed_state_feedback.py")==final["candidate_test_sha256"],"current test pin")
ck(sha(D/"map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl")==final["fixture_sha256"],"retained fixture pin")
ck(sha(H/"A09_PRE_FIX_COMPOSED_SOURCE.py")==freeze9["composed_source_sha256"],"A09 pre-fix source snapshot")
ck(sha(H/"A10_PRETEST_SOURCE.py")==freeze10["a09_source_sha256"],"A10 pretest source snapshot")
ck(sha(H/"A10_PRETEST_TEST.py")==freeze10["a09_test_sha256"],"A10 pretest test snapshot")
ck(replay["A09"]["baseline_false_pairs"]==8 and replay["A09"]["pre_fix_false_pairs"]==8 and replay["A09"]["repaired_false_pairs"]==0,"A09 red/green matrix")
ck(replay["A10"]["pre_fix_false_pairs"]==8 and replay["A10"]["repaired_false_pairs"]==0,"A10 red/green matrix")
ck(audit["audit"]=="PASS" and audit["checks"]==54 and audit["recomputed_mutations"]==16,"independent replay audit")
ck(audit["candidate_test_sha256"]==freeze11["candidate_test_sha256"],"A09/A10 auditor binds pre-A11 test snapshot")
ck(sha(H/"A11_TEST_PRE_ADDITION.py")==freeze11["candidate_test_sha256"],"A11 pre-test source snapshot")
ck(sha(REPO/"research/doom/map01_overlap_controller_v39.py")==freeze11["candidate_source_sha256"],"A11 candidate source pin")
ck(sha(H/"A11_FREEZE.json")==a11["freeze_sha256"],"A11 freeze binding")
ck(a11["baseline_false_pair_count"]==4 and a11["candidate_false_pair_count"]==0 and a11["candidate_closed_count"]==4,"A11 outcome matrix")
ck(a11audit["audit"]=="PASS" and a11audit["checks"]==13,"A11 independent audit")
ck(integration["base_sha"]==integration["merge_base"] and integration["merge_conflicts"]==0,"PR base integration identity")
ck(integration["validation"]["tests"]==41 and integration["validation"]["result"]=="PASS" and integration["package_verifier"]["result"]=="PASS","PR base integration validation")
ck("41 tests" in (H/"A11_FULL_SUITE.txt").read_text(encoding="utf-8") and "OK" in (H/"A11_FULL_SUITE.txt").read_text(encoding="utf-8"),"full local test log")
manifest=H/"SHA256SUMS_A09.txt"; entries={};valid=True
for line in manifest.read_text(encoding="utf-8-sig").splitlines():
 if "  " not in line:valid=False;continue
 digest,rel=line.split("  ",1);p=PurePosixPath(rel)
 if not rel or p.is_absolute() or ".." in p.parts or "\\" in rel or rel==manifest.name or rel in entries or len(digest)!=64:valid=False;continue
 target=(H/Path(*p.parts)).resolve()
 if not target.is_relative_to(H.resolve()) or not target.is_file():valid=False;continue
 entries[rel]=digest
ck(valid,"manifest syntax/containment/uniqueness")
for rel,digest in entries.items():ck(sha(H/Path(*PurePosixPath(rel).parts))==digest,"hash "+rel)
tracked={p.relative_to(H).as_posix() for p in H.rglob("*") if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith(".pyc")};tracked.discard(manifest.name)
ck(set(entries)==tracked,"manifest covers exact package contents")
failed=[n for ok,n in checks if not ok];print(json.dumps({"audit":"PASS" if not failed else "FAIL","checks":len(checks),"manifest_entries":len(entries),"errors":failed},indent=2));raise SystemExit(bool(failed))
