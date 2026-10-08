"""Create a safe public projection from the local-only original capture."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PRIVATE = ROOT / "RAW.private.json"
PUBLIC = ROOT / "RAW.json"
MARKER = (
    "PARTIAL_STATE=SAFE_YIELD; reason=effect_unavailable; "
    "completed_transitions=1; second_requested_input=NOT_RUN; "
    "saved_cells=13,41,533; next_row=BLANK"
)
SAFE_EXACT = {
    MARKER,
    "Run the registered protocol probe tool exactly once.",
    "{}",
    "MOCK_FINAL: partial evidence was delivered; no task completion is asserted.",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if PUBLIC.exists():
        raise SystemExit("refusing to replace existing public RAW.json")
    original_bytes = PRIVATE.read_bytes()
    original = json.loads(original_bytes)
    projected = dict(original)
    projected_requests = []
    for request in original.get("mock_responses_requests", []):
        item = dict(request)
        safe_texts = []
        redacted = []
        for text in request.get("text_fragments", []):
            allowed = MARKER if MARKER in text else text
            if allowed in SAFE_EXACT:
                safe_texts.append(allowed)
            else:
                raw = text.encode("utf-8")
                redacted.append({"sha256": digest(raw), "bytes": len(raw)})
        item["text_fragments"] = safe_texts
        item["redacted_text_fragment_count"] = len(redacted)
        item["redacted_text_fragments"] = redacted
        projected_requests.append(item)
    projected["mock_responses_requests"] = projected_requests
    projected["public_derivative"] = True
    projected["private_raw_sha256"] = digest(original_bytes)
    projected["private_runner_sha256"] = "49468acd7b89fb5d0769617f8487d6fbb09e9c409c8846a7a6140f09b386528a"
    PUBLIC.write_text(json.dumps(projected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"public_derivative": True, "private_raw_sha256": digest(original_bytes), "public_raw_sha256": digest(PUBLIC.read_bytes()), "requests": len(projected_requests), "redacted_text_fragments": sum(x["redacted_text_fragment_count"] for x in projected_requests)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
