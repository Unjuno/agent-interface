"""Single frozen host construction run. This runner does not call a backend."""
import hashlib
import json
from pathlib import Path

from candidate import preflight
from fixtures import CASES, RESOURCES

HERE=Path(__file__).resolve().parent


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    for name,digest in freeze["source_sha256"].items():
        if sha(HERE/name)!=digest:
            raise SystemExit("frozen source changed: "+name)
    registry=json.loads((HERE/"registry.json").read_text())
    plans=[]
    for case in CASES:
        plan=preflight(case["case_id"],case["ir"],case["assignments"],registry,RESOURCES)
        plans.append({"case_id":case["case_id"],**plan})
    out=HERE/"results"/"host-construction-01"
    out.mkdir(parents=True,exist_ok=False)
    raw={"schema":"verifier_registry_5273_raw.v3","allocation":freeze["allocation"],
        "base_commit":freeze["base_commit"],"freeze_sha256":sha(HERE/"FREEZE.json"),
        "registry_sha256":sha(HERE/"registry.json"),"fixtures_sha256":sha(HERE/"fixtures.py"),
        "parent_ir_candidate_sha256":freeze["parent_ir_candidate_sha256"],"plans":plans}
    encoded=json.dumps(raw,sort_keys=True,indent=2)+"\n"
    (out/"RAW.json").write_text(encoded)
    (out/"runner.stdout.txt").write_text(json.dumps({"status":"EXECUTED_HOST_CONSTRUCTION_ONLY","plans":len(plans)})+"\n")
    (out/"runner.stderr.txt").write_text("")
    print(json.dumps({"status":"EXECUTED_HOST_CONSTRUCTION_ONLY","plans":len(plans),"raw_sha256":hashlib.sha256(encoded.encode()).hexdigest()},sort_keys=True))


if __name__=="__main__": main()
