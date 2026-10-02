import hashlib
import json
from pathlib import Path

from axes_candidate import derive_axes

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for name, expected in freeze["package_sha256"].items():
        if digest(HERE / name) != expected:
            raise SystemExit(f"STOP_SOURCE_HASH:{name}")
    fixture_path = HERE / "fixture.json"
    if digest(fixture_path) != freeze["fixture_sha256"]:
        raise SystemExit("STOP_FIXTURE_HASH")
    fx = json.loads(fixture_path.read_text())
    result = {"allocation_id": freeze["allocation_id"],
              "source_main_sha": freeze["source_main_sha"],
              "candidate_invocations": 1,
              "fixture_sha256": digest(fixture_path),
              "cases": [{"case_id": row["case_id"],
                         "axes": derive_axes(row["candidate_view"])}
                        for row in fx["cases"]]}
    target = HERE / "candidate_result.json"
    if target.exists():
        raise SystemExit("STOP_CANDIDATE_OUTPUT_EXISTS")
    target.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"allocation_id": result["allocation_id"],
                      "candidate_invocations": 1,
                      "case_count": len(result["cases"]),
                      "status": "CANDIDATE_COMPLETE"}, sort_keys=True))


if __name__ == "__main__":
    main()
