"""One-shot candidate-vs-retained-auditor boolean-canary runner."""
import copy
import hashlib
import json
from pathlib import Path

import audit_hardened
import candidate


RAW_PATH = Path("/input/RAW.json")
OUT_PATH = Path("/out/runner_result.json")
CANARIES = (
    ("cost.A", ("cost", "A"), True),
    ("drift_grid[0]", ("drift_grid", 0), False),
    ("distributions[-1].alpha", ("distributions", -1, "alpha"), True),
    ("rows[1].state_id", ("distributions", 0, "rows", 1, "state_id"), True),
    ("rows[0].truth.A", ("distributions", 0, "rows", 0, "truth", "A"), 0),
    ("rows[0].NAIVE.evaluations", ("distributions", 0, "rows", 0,
                                  "NAIVE", "evaluations"), True),
    ("rows[0].NAIVE.semantic_mismatches",
     ("distributions", 0, "summaries", "NAIVE", "semantic_mismatches"), False),
)


def set_path(document, path, value):
    target = document
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def main():
    raw_bytes = RAW_PATH.read_bytes()
    raw = json.loads(raw_bytes.decode("utf-8"), parse_constant=audit_hardened.reject_nonfinite)
    baseline = audit_hardened.audit_document(raw)
    rows = []
    for label, path, replacement in CANARIES:
        mutated = copy.deepcopy(raw)
        set_path(mutated, path, replacement)
        try:
            audit_hardened.audit_document(mutated)
            baseline_accepts = True
        except Exception:
            baseline_accepts = False
        try:
            candidate.audit_document(mutated, raw, audit_hardened)
            candidate_accepts = True
            candidate_reason = "accepted"
        except Exception as exc:
            candidate_accepts = False
            candidate_reason = type(exc).__name__ + ":" + str(exc)
        mutation_bytes = json.dumps(mutated, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False).encode("utf-8")
        rows.append({"canary": label, "path": list(path),
                     "replacement_type": type(replacement).__name__,
                     "mutation_sha256": hashlib.sha256(mutation_bytes).hexdigest(),
                     "baseline_accepts": baseline_accepts,
                     "candidate_accepts": candidate_accepts,
                     "candidate_reason": candidate_reason})
    result = {
        "schema": "predicate-order-audit-typehash-formal-v1",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "raw_bytes": len(raw_bytes),
        "baseline": baseline,
        "canaries": rows,
        "decision": "PASS_AUDIT_BOUNDARY_REPAIRED_SCOPED"
        if baseline["rows"] == 336 and len(rows) == 7 and
        all(row["baseline_accepts"] and not row["candidate_accepts"] for row in rows)
        else "FAIL_DECLARED_GATE",
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
    print(result["decision"])


if __name__ == "__main__":
    main()
