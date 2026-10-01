import hashlib
import json
from pathlib import Path

from candidate_v2 import analyze_sources

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent


def run():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    frozen_package = freeze["package_sha256"]
    for name in ("candidate_v2.py", "run_candidate_v2.py"):
        observed = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        if observed != frozen_package[name]:
            raise SystemExit(f"STOP_CANDIDATE_SOURCE_HASH_MISMATCH:{name}")
    predecessor = hashlib.sha256((PARENT / "candidate.py").read_bytes()).hexdigest()
    predecessor_freeze = hashlib.sha256((PARENT / "FREEZE.json").read_bytes()).hexdigest()
    if (predecessor != freeze["predecessor_candidate_sha256"]
            or predecessor_freeze != freeze["predecessor_freeze_sha256"]):
        raise SystemExit("STOP_PREDECESSOR_SOURCE_HASH_MISMATCH")
    sources = {}
    for name, item in freeze["inputs"].items():
        data = (PARENT / "inputs" / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise SystemExit(f"STOP_INPUT_HASH_MISMATCH:{name}")
        sources[name] = data.decode("utf-8")
    result = analyze_sources(sources)
    result["allocation_id"] = freeze["allocation_id"]
    result["source_main_sha"] = freeze["source_main_sha"]
    result["source_sha256"] = {name: item["sha256"]
                               for name, item in freeze["inputs"].items()}
    result["candidate_invocations"] = 1
    result["retries"] = 0
    (HERE / "candidate_result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    run()
