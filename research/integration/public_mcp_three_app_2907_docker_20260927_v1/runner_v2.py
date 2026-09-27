"""Additive caller adapter for the retained v1 runner; never edits v1 bytes."""
import os
from pathlib import Path

import runner as frozen_runner


_text_payload = frozen_runner.text_payload
_save_mcp_response = frozen_runner.save_mcp_response


def normalize_public_receipt(result):
    payload = _text_payload(result)
    if payload.get("schema") != "agent-interface/review-v1":
        return payload
    receipt = payload.get("receipt", {})
    report = receipt.get("report", {})
    raw = receipt.get("source", {}).get("raw_report", {})
    if (receipt.get("schema") != "agent-interface/receipt-view-v1" or
            not isinstance(raw, dict) or not isinstance(report, dict)):
        raise AssertionError("PUBLIC_RECEIPT_V1_SHAPE_UNRECOGNIZED")
    payload["status"] = raw.get("status")
    payload["observation"] = raw
    payload["input_dispatched"] = raw.get("input_dispatched")
    payload["side_effect_authority"] = raw.get("side_effect_authority")
    payload["session"] = payload.get("session") or raw.get("session")
    return payload


def save_with_image_digest(path, result):
    metadata = _save_mcp_response(path, result)
    images = [row for row in metadata.get("blocks", []) if row.get("type") == "image"]
    if len(images) == 1:
        metadata["image_sha256"] = images[0]["sha256"]
    return metadata


frozen_runner.text_payload = normalize_public_receipt
frozen_runner.save_mcp_response = save_with_image_digest
frozen_runner.OUT = Path(os.environ.get("OUTPUT_DIR", "/evidence/formal02"))

if __name__ == "__main__":
    raise SystemExit(frozen_runner.main())
