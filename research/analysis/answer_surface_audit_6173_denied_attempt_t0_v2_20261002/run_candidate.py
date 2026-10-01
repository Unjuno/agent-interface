import hashlib
import json
from pathlib import Path

from candidate import classify

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for name, expected in freeze["package_sha256"].items():
        if digest(HERE / name) != expected:
            raise SystemExit(f"STOP_SOURCE_HASH:{name}")
    data_path = HERE / "candidate_input.json"
    if digest(data_path) != freeze["candidate_input_sha256"]:
        raise SystemExit("STOP_INPUT_HASH:candidate_input.json")
    data = json.loads(data_path.read_text())
    result = {"allocation_id": freeze["allocation_id"],
              "source_main_sha": freeze["source_main_sha"],
              "candidate_invocations": 1,
              "input_sha256": digest(data_path),
              "cases": [{"case_id": row["case_id"],
                         "classification": classify(row["view"])}
                        for row in data["cases"]]}
    target = HERE / "candidate_result.json"
    if target.exists():
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    target.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"allocation_id": result["allocation_id"],
                      "candidate_invocations": 1,
                      "case_count": len(result["cases"]),
                      "status": "CANDIDATE_COMPLETE"}, sort_keys=True))


if __name__ == "__main__":
    main()
