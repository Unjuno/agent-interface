#!/usr/bin/env python3
"""Independent standard-library audit of the CPU-only construction receipt."""
import hashlib
import json
from pathlib import Path

EXPECTED_SUPPORT = "bf4d64cf826ea2d727990bd799d7e6d0f813a97a64119751e05d22a819fdf785"
EXPECTED_VOCABULARY = ["C0", "C1", "C2", "C3", "C4", "C5"]


def validate(record):
    assert record["schema"] == "issue-4821-label-abi-construction-v1"
    assert record["support_sha256"] == EXPECTED_SUPPORT
    assert record["support_rows"] == 256
    assert record["vocabulary"] == EXPECTED_VOCABULARY
    assert record["encoded_dtype"] == "int64"
    assert record["encoded_ids"] == list(range(6))
    assert record["split_sizes"] == [204, 52, 204, 52]
    assert record["split_ids"] == list(range(6))
    assert record["model_loaded"] is False
    assert record["gpu_requested"] is False


def main():
    support = Path("/inputs/support.csv").read_bytes()
    if hashlib.sha256(support).hexdigest() != EXPECTED_SUPPORT:
        raise SystemExit("SUPPORT_HASH_MISMATCH")
    record = json.loads(Path("/evidence/DIAGNOSTIC_RESULT.json").read_text(encoding="utf-8"))
    validate(record)
    controls = {
        "support_hash": {**record, "support_sha256": "0" * 64},
        "vocabulary": {**record, "vocabulary": list(reversed(EXPECTED_VOCABULARY))},
        "encoded_dtype": {**record, "encoded_dtype": "object"},
        "missing_class": {**record, "encoded_ids": [0, 1, 2, 3, 4]},
        "split_sizes": {**record, "split_sizes": [200, 56, 204, 52]},
        "model_load": {**record, "model_loaded": True},
        "gpu_request": {**record, "gpu_requested": True},
    }
    for name, altered in controls.items():
        try:
            validate(altered)
        except (AssertionError, KeyError, TypeError):
            continue
        raise SystemExit("CONTROL_ACCEPTED:" + name)
    receipt = {
        "schema": "issue-4821-label-abi-independent-audit-v1",
        "pass": True,
        "errors": [],
        "corruption_controls_rejected": len(controls),
        "support_sha256": EXPECTED_SUPPORT,
        "audited_schema": record["schema"],
    }
    Path("/out/AUDIT.json").write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
