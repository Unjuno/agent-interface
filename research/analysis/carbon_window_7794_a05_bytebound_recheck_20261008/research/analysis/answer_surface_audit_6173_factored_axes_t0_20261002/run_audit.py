import hashlib
import json
from pathlib import Path

from audit_axes import audit

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for name, expected in freeze["package_sha256"].items():
        if digest(HERE / name) != expected:
            raise SystemExit(f"STOP_AUDIT_SOURCE_HASH:{name}")
    fixture_path = HERE / "fixture.json"
    if digest(fixture_path) != freeze["fixture_sha256"]:
        raise SystemExit("STOP_AUDIT_FIXTURE_HASH")
    result_path = HERE / "candidate_result.json"
    if not result_path.exists():
        raise SystemExit("STOP_CANDIDATE_RESULT_MISSING")
    result = audit(json.loads(result_path.read_text()),
                   json.loads(fixture_path.read_text()),
                   digest(fixture_path), freeze["allocation_id"],
                   freeze["source_main_sha"])
    result.update({"allocation_id": freeze["allocation_id"],
                   "source_main_sha": freeze["source_main_sha"],
                   "candidate_result_sha256": digest(result_path),
                   "auditor_invocations": 1, "retries": 0})
    target = HERE / "audit_result.json"
    if target.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_EXISTS")
    target.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_FACTORED_AXES" else 1)


if __name__ == "__main__":
    main()
