"""Create a source/input freeze; running it does not execute the formal cases."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ("candidate.py", "oracle.py", "registry.json", "cases.json", "test_registry.py", "run_formal.py", "audit.py", "PLAN.md")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    obj = {
        "schema": "verifier_registry_5273_freeze.v1",
        "issue": 5273,
        "base_commit": "322faf504a5ac993b092f154733d83bc13767e60",
        "branch": "research/verifier-registry-5273-t0-20260930",
        "allocation": "verifier-registry-5273-t0-20260930-01",
        "authority": "none",
        "formal_invocations_at_freeze": 0,
        "container_status": "STOP_NO_EXPLICIT_RESOURCE_LEASE",
        "formal_source_sha256": {name: sha(HERE / name) for name in FILES},
    }
    (HERE / "FREEZE.json").write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n")
    print(json.dumps(obj, sort_keys=True))


if __name__ == "__main__":
    main()
