"""One frozen matrix invocation for occurrence-identified key intervals."""
import hashlib
import json
from pathlib import Path

from occurrence_ledger import summarize

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases.json"
OUT = HERE / "results" / "t0-01" / "raw.json"


def main():
    case_bytes = CASES.read_bytes()
    bundle = json.loads(case_bytes.decode("utf-8"))
    results = [{"case_id": case["case_id"], "candidate_result": summarize(case["events"])}
               for case in bundle["cases"]]
    payload = {
        "schema": "map01-occurrence-key-occupancy-raw-v1",
        "allocation_id": bundle["allocation_id"],
        "main_sha": "f0139613cb96d5f2d84e803b75961dff549d58c8",
        "cases_sha256": hashlib.sha256(case_bytes).hexdigest(),
        "candidate_invocations": 1,
        "retries": 0,
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
