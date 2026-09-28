"""Run v2 candidate and oracle against immutable v1 raw cases."""
import hashlib
import json
from pathlib import Path
from contract import classify
from oracle import oracle

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "map01_task_effect_contract_5126_v1" / "result.json"
INPUT_SHA256 = "536de27a25cdc7b9936235dc1ef900cf174f2acbf16239a696474ede5f69fa9f"


def main():
    data = INPUT.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != INPUT_SHA256:
        raise SystemExit(f"STOP_INPUT_HASH_MISMATCH:{digest}")
    original = json.loads(data)
    rows = []
    for old in original["cases"]:
        expected = old["expected_task_effect"]
        if old["case_id"] == "cross_plane_event_id_collision":
            expected = "UNRESOLVED_DUPLICATE_SOURCE_EVENT"
        raw = old["raw"]
        rows.append({"case_id": old["case_id"], "raw": raw, "expected_task_effect": expected,
                     "candidate": classify(raw), "oracle": oracle(raw)})
    output = {"schema": "map01-task-effect-contract-result-v3", "issue": 5126,
              "input_corpus_sha256": digest, "input_authority": False, "live_calls": 0, "cases": rows}
    path = HERE / "result.json"
    path.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"cases": len(rows),
                      "candidate_oracle_mismatches": sum(r["candidate"] != r["oracle"] for r in rows),
                      "expected_mismatches": sum(r["candidate"]["task_effect"] != r["expected_task_effect"] for r in rows),
                      "cross_plane_collision_status": next(r["candidate"]["task_effect"] for r in rows
                                                             if r["case_id"] == "cross_plane_event_id_collision"),
                      "input_corpus_sha256": digest}, sort_keys=True))


if __name__ == "__main__":
    main()
