"""Write the source/input freeze for the v2 host construction allocation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ("PLAN.md", "candidate.py", "oracle.py", "registry.json", "cases.json", "test_registry.py", "run_formal.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parent = HERE.parent / "verification_ir_5268_v1" / "candidate.py"
    obj = {
        "schema": "verifier_registry_5273_freeze.v2",
        "issue": 5273,
        "allocation": "verifier-registry-5273-t0-v2-20260930-01",
        "base_commit": "c12e6079f82d1604a9f9a08445a314e4d59d8846",
        "branch": "research/verifier-registry-5273-t0-v2-20260930",
        "authority": "none",
        "execution_status": "HOST_CONSTRUCTION_ONLY_NO_CONTAINER_LEASE",
        "formal_container_invocations": 0,
        "source_sha256": {name: sha(HERE / name) for name in FILES},
        "parent_ir_candidate_sha256": sha(parent),
    }
    path = HERE / "FREEZE.json"
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"freeze_sha256": sha(path), "source_sha256": obj["source_sha256"],
                      "parent_ir_candidate_sha256": obj["parent_ir_candidate_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
