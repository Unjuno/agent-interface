"""Single allocated v4 synthetic run over the pinned v1 raw corpus."""
import hashlib
import json
from pathlib import Path
from contract import classify
from oracle import oracle

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "map01_task_effect_contract_5126_v1" / "result.json"
INPUT_SHA256 = "536de27a25cdc7b9936235dc1ef900cf174f2acbf16239a696474ede5f69fa9f"


def make_rows():
    raw_bytes = INPUT.read_bytes()
    input_sha = hashlib.sha256(raw_bytes).hexdigest()
    if input_sha != INPUT_SHA256:
        raise ValueError("STOP_INPUT_HASH_MISMATCH:" + input_sha)
    source = json.loads(raw_bytes)
    rows = []
    for old in source["cases"]:
        expected = old["expected_task_effect"]
        if old["case_id"] == "cross_plane_event_id_collision":
            expected = "UNRESOLVED_DUPLICATE_SOURCE_EVENT"
        raw = old["raw"]
        rows.append({"case_id": old["case_id"], "raw": raw, "expected_task_effect": expected,
                     "candidate": classify(raw), "oracle": oracle(raw)})
    return input_sha, rows


def main():
    input_sha, rows = make_rows()
    output = {"schema": "map01-task-effect-contract-result-v5",
              "allocation": "MAP01-TASK-EFFECT-LINEAGE-5126-20260928-04",
              "issue": 5126, "input_corpus_sha256": input_sha,
              "input_authority": False, "live_calls": 0, "cases": rows}
    path = HERE / "result.json"
    path.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"cases": len(rows), "candidate_oracle_mismatches":
                      sum(r["candidate"] != r["oracle"] for r in rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
