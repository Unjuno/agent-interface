"""Audit that the public record retains the marker/image without raw prompt text."""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
RAW = ROOT / "RAW.json"
AUDIT = ROOT / "PUBLICATION_AUDIT.json"
IMAGE_SHA = "6331fd4bb0f62dbb6d8492e0c71a4ad6bf1b98091f39b452e2279e7cfd3e6bcf"
MARKER = (
    "PARTIAL_STATE=SAFE_YIELD; reason=effect_unavailable; "
    "completed_transitions=1; second_requested_input=NOT_RUN; "
    "saved_cells=13,41,533; next_row=BLANK"
)
SAFE_TEXTS = {
    MARKER,
    "Run the registered protocol probe tool exactly once.",
    "{}",
    "MOCK_FINAL: partial evidence was delivered; no task completion is asserted.",
}


def main() -> int:
    if AUDIT.exists():
        raise SystemExit("refusing to replace existing PUBLICATION_AUDIT.json")
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    requests = raw.get("mock_responses_requests", [])
    errors = []
    if raw.get("public_derivative") is not True:
        errors.append("public derivative flag")
    if len(requests) != 2:
        errors.append("request count")
    if raw.get("private_raw_sha256") != "00dc26ec7d69abeb5f805166c738c8a0ce769fd92e9229407c6e4d10ed7c0800":
        errors.append("private raw provenance pin")
    second = requests[1] if len(requests) > 1 else {}
    if MARKER not in second.get("text_fragments", []):
        errors.append("partial marker absent")
    if IMAGE_SHA not in second.get("data_image_sha256s", []):
        errors.append("image bytes absent")
    for request in requests:
        texts = request.get("text_fragments", [])
        if any(text not in SAFE_TEXTS for text in texts):
            errors.append("non-allowlisted public text")
        redacted = request.get("redacted_text_fragments", [])
        if any(set(item) != {"sha256", "bytes"} or len(item["sha256"]) != 64 for item in redacted):
            errors.append("redaction record shape")
        if request.get("redacted_text_fragment_count") != len(redacted):
            errors.append("redaction count")
    result = {
        "disposition": "PASS_PUBLIC_REDACTION_SCOPED" if not errors else "FAIL_PUBLIC_REDACTION_SCOPED",
        "errors": errors,
        "request_count": len(requests),
        "partial_marker_present": MARKER in second.get("text_fragments", []),
        "image_sha256_present": IMAGE_SHA in second.get("data_image_sha256s", []),
        "redacted_text_fragments": sum(r.get("redacted_text_fragment_count", 0) for r in requests),
        "scope": "public projection allowlist and retained marker/image identity only",
    }
    AUDIT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
