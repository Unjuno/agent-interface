"""Candidate projection for the A02 intake stream."""
from __future__ import annotations
import hashlib, json
from collections import Counter
from pathlib import Path

def project(data: dict, raw: bytes) -> dict:
    rows = data["rows"]
    intake = [x for x in rows if x["kind"] == "intake"]
    started = [x for x in rows if x["kind"] == "test" and x["test_started"]]
    eligible = [x for x in started if x["statistical_eligible"]]
    deterministic = [x for x in rows if x["kind"] == "deterministic"]
    return {
        "schema":"portfolio-intake-ledger-v1", "fixture_id":data["fixture_id"],
        "input_sha256":hashlib.sha256(raw).hexdigest(),
        "intake":{"count":len(intake),"screen_counts":dict(sorted(Counter(x["screen"] for x in intake).items())),"ids":[x["id"] for x in intake]},
        "started_opportunities":[{"id":x["id"],"claim_id":x["claim_id"],"outcome":x["outcome"],"abandoned_after_interim":x["abandoned_after_interim"],"statistical_eligible":x["statistical_eligible"]} for x in started],
        "statistical_family":[{"id":x["id"],"claim_id":x["claim_id"],"p_value":x["p_value"]} for x in eligible],
        "deterministic":[{"id":x["id"],"outcome":x["outcome"],"hard_safety":x["hard_safety"]} for x in deterministic],
        "counts":{"all_rows":len(rows),"screened_out_not_tested":len(intake),"started_test_opportunities":len(started),"statistical_family_size":len(eligible),"deterministic_rows":len(deterministic),"started_negative_abandoned":sum(x["outcome"]=="TEST_STARTED_FAIL" and x["abandoned_after_interim"] for x in started)}
    }

def main() -> None:
    root=Path(__file__).resolve().parent; raw=(root/"formal_input.json").read_bytes(); data=json.loads(raw)
    result=project(data,raw)
    (root/"candidate_raw.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result["counts"],sort_keys=True))

if __name__=="__main__": main()
