from pathlib import Path
import hashlib,json,re
p=Path(__file__).resolve().parent;c=json.loads((p/"conditions.json").read_text(encoding="utf-8"));runner=(p/"run_standard_calculator.py").read_text(encoding="utf-8-sig");ids=sorted(set(re.findall(r"win32-standard-calculator-task-20261024-r14-[0-9a-f]{8}",runner)))
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
ok=all(sha(p/n)==h for h,n in (line.split("  ",1) for line in (p/"FROZEN_SHA256SUMS").read_text(encoding="ascii").splitlines()))
runtime_files=[str(x.relative_to(p)) for x in (p/"run").rglob("*") if x.is_file() and x.name!="audit.json"]
a={"schema":"win32-standard-calculator-r14-audit-v1","attempt_id":c["attempt_id"],"frozen_manifest_matches":ok,"runner_attempt_ids":ids,"conditions_runner_id_match":bool(ids) and c["attempt_id"] in ids,"runtime_receipt_files":runtime_files,"dispatch_started":False,"disposition":"PRELAUNCH_STOP: frozen ID mismatch caught before execution."}
assert ok and ids and c["attempt_id"] not in ids and not runtime_files
(p/"run"/"audit.json").write_text(json.dumps(a,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(a,ensure_ascii=True,indent=2))
