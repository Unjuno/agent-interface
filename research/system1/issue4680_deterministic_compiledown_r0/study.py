import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import oracle
import policy

IMAGE_ID = "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
ALLOCATION = "issue4680-deterministic-compiledown-20260927-01"
PACKAGE = {
    "skill_id": "bounded-progress-v1", "intent_version": 1,
    "allowed_actions": sorted(policy.ACTIONS), "forbidden_effects": ["SUBMIT"],
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--freeze", required=True)
    args = ap.parse_args()
    frozen = json.loads(Path(args.freeze).read_text(encoding="utf-8"))
    for name, expected in frozen["source_sha256"].items():
        if sha(Path("/study", name).read_bytes()) != expected:
            raise SystemExit("STOP_SOURCE_HASH_MISMATCH:" + name)
    table = policy.compile_table(PACKAGE)
    rows = policy.make_rows()
    records = []
    for row in rows:
        direct = policy.direct(PACKAGE, row)
        compiled = policy.compiled(table, row)
        expected = oracle.expected(row)
        records.append({"row": row, "direct": direct, "compiled": compiled,
                        "oracle": expected, "match": direct == compiled == expected})

    initial = json.dumps(PACKAGE, sort_keys=True, separators=(",", ":")).encode()
    invalid = dict(PACKAGE)
    invalid["allowed_actions"] = sorted(policy.ACTIONS | {"SUBMIT"})
    after, activated = policy.activate(initial, invalid)
    controls = {
        "missing_yields": policy.direct(PACKAGE, {"intent":"TRACK","evidence":"MISSING","progressing":True,"completed":False,"generation_fresh":True,"forbidden_effect":False}) == "YIELD",
        "ambiguous_yields": policy.direct(PACKAGE, {"intent":"TRACK","evidence":"AMBIGUOUS","progressing":True,"completed":False,"generation_fresh":True,"forbidden_effect":False}) == "YIELD",
        "stale_evidence_yields": policy.direct(PACKAGE, {"intent":"TRACK","evidence":"STALE","progressing":True,"completed":False,"generation_fresh":True,"forbidden_effect":False}) == "YIELD",
        "stale_generation_yields": policy.direct(PACKAGE, {"intent":"TRACK","evidence":"CLEAR","progressing":True,"completed":False,"generation_fresh":False,"forbidden_effect":False}) == "YIELD",
        "forbidden_effect_yields": policy.direct(PACKAGE, {"intent":"TRACK","evidence":"CLEAR","progressing":True,"completed":False,"generation_fresh":True,"forbidden_effect":True}) == "YIELD",
        "invalid_intent_yields": policy.direct(PACKAGE, {"intent":"UNKNOWN","evidence":"CLEAR","progressing":True,"completed":False,"generation_fresh":True,"forbidden_effect":False}) == "YIELD",
        "authority_expansion_rejected": not policy.valid_package(invalid),
        "failed_activation_preserves_active": not activated and after == initial and sha(after) == sha(initial),
    }
    result = {
        "schema": "issue4680-deterministic-compiledown-r0",
        "allocation": ALLOCATION,
        "image_id": IMAGE_ID,
        "python": sys.version,
        "platform": platform.platform(),
        "source_sha256": frozen["source_sha256"],
        "row_count": len(records),
        "unique_state_count": len({tuple(r["row"].values()) for r in records}),
        "mismatch_count": sum(not r["match"] for r in records),
        "records": records,
        "controls": controls,
        "decision": "PASS_DETERMINISTIC_COMPILEDOWN_EQUIVALENCE_SCOPED" if len(records) == 256 and all(r["match"] for r in records) and all(controls.values()) else "FAIL_DETERMINISTIC_COMPILEDOWN",
        "formal_study_invocations": 1,
        "latency_measured": False,
        "adaptation_prerequisite_met": False,
        "fast_backend_prerequisite_met": False,
    }
    Path(args.output).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
