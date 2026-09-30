"""Write immutable source/input manifest before the one host construction run."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
FILES=("PLAN.md","candidate.py","fixtures.py","oracle.py","registry.json","test_registry.py","run_formal.py")


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parent=HERE.parent/"verification_ir_5268_v1"/"candidate.py"
    data={"schema":"verifier_registry_5273_freeze.v3","issue":5273,
        "allocation":"verifier-registry-5273-t0-v3-20260930-01",
        "base_commit":"4e2c0cf6241e3068bbc1afde8c97206c6b731a1b",
        "branch":"research/verifier-registry-5273-t0-v3-20260930",
        "authority":"none","execution_status":"HOST_CONSTRUCTION_ONLY_NO_CONTAINER_LEASE",
        "formal_container_invocations":0,
        "source_sha256":{name:sha(HERE/name) for name in FILES},
        "parent_ir_candidate_sha256":sha(parent)}
    target=HERE/"FREEZE.json"
    target.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"freeze_sha256":sha(target),"parent_ir_candidate_sha256":data["parent_ir_candidate_sha256"],"sources":data["source_sha256"]},sort_keys=True))


if __name__=="__main__": main()
