"""Compare committed v3 corpus bytes with the v5 frozen corpus copy."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
V3_PATH = Path(
    "research/system1/typed_readout_decision_equivalence_1014_v3/"
    "corpus_source/corpus.jsonl"
)
V5_PATH = Path("research/system1/typed_readout_precision_boundary_1014_v5/corpus.jsonl")
MAIN_SHA = "12d15dd81c47e8af80abd3172d67d934452f36ca"
FROZEN_SHA256 = "85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c"


def load_records(raw: bytes) -> list[object]:
    return [json.loads(line) for line in raw.splitlines() if line]


def describe(path: Path, raw: bytes) -> dict[str, object]:
    records = load_records(raw)
    crlf = raw.count(b"\r\n")
    return {
        "path": path.as_posix(),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "crlf_pairs": crlf,
        "lf_only": raw.count(b"\n") - crlf,
        "final_lf": raw.endswith(b"\n"),
        "json_records": len(records),
    }


def run() -> dict[str, object]:
    # Read immutable committed blobs so sparse-checkout state cannot affect input bytes.
    v3 = subprocess.check_output(["git", "show", f"{MAIN_SHA}:{V3_PATH.as_posix()}"], cwd=ROOT)
    v5 = subprocess.check_output(["git", "show", f"{MAIN_SHA}:{V5_PATH.as_posix()}"], cwd=ROOT)
    v3_normalized = v3.replace(b"\r\n", b"\n")
    v5_normalized = v5.replace(b"\r\n", b"\n")
    v3_lines = v3_normalized.splitlines()
    v5_lines = v5_normalized.splitlines()
    changed_lines = sum(a != b for a, b in zip(v3_lines, v5_lines))
    v3_records = load_records(v3)
    v5_records = load_records(v5)
    v5_sha = hashlib.sha256(v5).hexdigest()
    eol_only = (
        v3 != v5
        and v3_normalized == v5_normalized
        and len(v3_lines) == len(v5_lines)
        and changed_lines == 0
        and v3_records == v5_records
    )
    return {
        "schema": "typed-readout-corpus-eol-audit-v1",
        "main_sha": MAIN_SHA,
        "hypothesis": (
            "The #4871 frozen corpus hash mismatch is explained solely by "
            "LF versus CRLF serialization; parsed JSONL records are identical."
        ),
        "status": "PASS_CORPUS_CONTENT_EQUAL_EOL_ONLY_SCOPED" if eol_only else "FAIL_CONTENT_DIFFERS",
        "files": {
            "main_v3": describe(V3_PATH, v3),
            "frozen_v5": describe(V5_PATH, v5),
        },
        "comparison": {
            "raw_bytes_equal": v3 == v5,
            "raw_byte_delta_v5_minus_v3": len(v5) - len(v3),
            "eol_normalized_equal": v3_normalized == v5_normalized,
            "normalized_line_count_v3": len(v3_lines),
            "normalized_line_count_v5": len(v5_lines),
            "changed_normalized_lines": changed_lines,
            "parsed_records_equal": v3_records == v5_records,
            "record_count": len(v3_records),
            "v5_matches_issue_4871_frozen_sha256": v5_sha == FROZEN_SHA256,
        },
        "interpretation": (
            "The original byte-hash STOP remains valid: byte identity failed. "
            "This audit shows the observed difference is line-ending-only; "
            "it does not rewrite that allocation or its STOP. The distinct #4912 v5 "
            "allocation already used the exact frozen bytes and has its own GPU "
            "construction result and raw-only audit."
        ),
        "scope": (
            "Read-only corpus provenance comparison only; no model, tokenizer, "
            "GPU/CUDA, Docker/OrbStack, or formal allocation."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
