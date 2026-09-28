"""Independent byte/record verifier; deliberately does not import reproduce.py."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
SOURCE_COMMIT = "12d15dd81c47e8af80abd3172d67d934452f36ca"
V3_PATH = "research/system1/typed_readout_decision_equivalence_1014_v3/corpus_source/corpus.jsonl"
V5_PATH = "research/system1/typed_readout_precision_boundary_1014_v5/corpus.jsonl"
RESULT = PACKAGE / "result.json"


def normalized_equal(left: bytes, right: bytes) -> bool:
    """Normalize only CRLF pairs, leaving every other byte significant."""
    return left.replace(b"\r\n", b"\n") == right.replace(b"\r\n", b"\n")


def verify() -> dict[str, object]:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    old_bytes = subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{V3_PATH}"], cwd=ROOT)
    frozen_bytes = subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{V5_PATH}"], cwd=ROOT)
    old_records = [json.loads(line) for line in old_bytes.splitlines() if line]
    frozen_records = [json.loads(line) for line in frozen_bytes.splitlines() if line]
    actual = {
        "v3_sha256": hashlib.sha256(old_bytes).hexdigest(),
        "v5_sha256": hashlib.sha256(frozen_bytes).hexdigest(),
        "v3_bytes": len(old_bytes),
        "v5_bytes": len(frozen_bytes),
        "v3_crlf": old_bytes.count(b"\r\n"),
        "v5_crlf": frozen_bytes.count(b"\r\n"),
        "normalized_equal": normalized_equal(old_bytes, frozen_bytes),
        "records_equal": old_records == frozen_records,
        "record_count": len(old_records),
    }
    expected = result["files"]
    checks = {
        "status": result["status"] == "PASS_CORPUS_CONTENT_EQUAL_EOL_ONLY_SCOPED",
        "v3_hash": actual["v3_sha256"] == expected["main_v3"]["sha256"],
        "v5_hash": actual["v5_sha256"] == expected["frozen_v5"]["sha256"],
        "v3_length": actual["v3_bytes"] == expected["main_v3"]["bytes"],
        "v5_length": actual["v5_bytes"] == expected["frozen_v5"]["bytes"],
        "line_ending_only": actual["normalized_equal"] and actual["v3_sha256"] != actual["v5_sha256"],
        "parsed_records": actual["records_equal"] and actual["record_count"] == 64,
        "result_claims": result["comparison"]["parsed_records_equal"] is True
        and result["comparison"]["eol_normalized_equal"] is True,
    }
    if not all(checks.values()):
        raise SystemExit(json.dumps({"status": "FAIL", "checks": checks, "actual": actual}, indent=2))

    mutation = bytearray(old_bytes)
    mutation[0] ^= 1
    mutation_rejected = not normalized_equal(bytes(mutation), frozen_bytes)
    if not mutation_rejected:
        raise SystemExit("FAIL: non-EOL byte mutation was not detected")
    return {
        "status": "AUDIT_PASS_CORPUS_EOLO_ONLY",
        "checks": checks,
        "actual": actual,
        "mutation_controls": {"single_non_eol_byte_change_rejected": mutation_rejected},
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
