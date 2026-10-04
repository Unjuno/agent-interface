from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
RAW_ROOT = PKG / "replay_raw"
RUNS = ("a01_20261005", "a02_20261005")


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def evidence_bytes(path: Path) -> bytes:
    # Git's core.autocrlf may materialize these frozen JSONL/JSON text files with CRLF.
    # Their recorded digests describe the committed LF bytes.
    return path.read_bytes().replace(b"\r\n", b"\n")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def audit_bindings() -> dict:
    for line in (PKG / "REPLAY_SHA256SUMS").read_text(encoding="ascii").splitlines():
        expected, rel = line.split("  ", 1)
        require(digest_bytes(evidence_bytes(RAW_ROOT / rel)) == expected, f"raw replay hash mismatch: {rel}")
    baseline_output = json.loads((PKG / "REPLAY_AUDIT.json").read_text(encoding="utf-8"))
    require(baseline_output.get("status") == "PASS", "preserved baseline replay output is not PASS")
    checked = 0
    for run_id in RUNS:
        raw = RAW_ROOT / run_id
        events = [json.loads(line) for line in (raw / "host-events.jsonl").read_text(encoding="utf-8").splitlines()]
        for attempt in range(1, 5):
            reply_path = raw / f"reply-{attempt}.json"
            reply_bytes = evidence_bytes(reply_path)
            reply_sha = digest_bytes(reply_bytes)
            reply = json.loads(reply_bytes)
            review = json.loads((raw / f"review-{attempt}.json").read_text(encoding="utf-8"))
            texts = [block["text"] for block in reply["result"]["content"] if block.get("type") == "text"]
            images = [block for block in reply["result"]["content"] if block.get("type") == "image"]
            require(len(texts) == 1 and len(images) == 1, f"{run_id} attempt {attempt}: expected one reply text and image")
            meta = json.loads(texts[0])
            source = meta["source"]
            call_id = meta["call_id"]
            sequence = source["sequence"]
            observation_id = source["observation_id"]

            require(review["reply_sha256"] == reply_sha, f"{run_id} attempt {attempt}: review reply digest mismatch")
            require(review["tool"] == reply["tool"], f"{run_id} attempt {attempt}: review tool mismatch")
            require(review["relay_id"] == reply["id"], f"{run_id} attempt {attempt}: review relay id mismatch")
            require(review["call_id"] == call_id, f"{run_id} attempt {attempt}: review call id mismatch")
            require(review["source_sequence"] == sequence, f"{run_id} attempt {attempt}: review sequence mismatch")
            require(review["observation_id"] == observation_id, f"{run_id} attempt {attempt}: review observation id mismatch")
            image_sha = digest_bytes(base64.b64decode(images[0]["data"], validate=True))
            receipt_images = review["images"]
            require(len(receipt_images) == 1, f"{run_id} attempt {attempt}: expected one reviewed image")
            require(receipt_images[0]["mime_type"] == images[0]["mimeType"], f"{run_id} attempt {attempt}: review image MIME mismatch")
            require(receipt_images[0]["sha256"] == image_sha, f"{run_id} attempt {attempt}: review image digest mismatch")

            for kind in ("reply_available", "presentation_started", "presentation_callbacks_completed", "review_recorded"):
                matches = [event for event in events if event.get("kind") == kind and event.get("attempt") == attempt]
                require(len(matches) == 1, f"{run_id} attempt {attempt}: expected one {kind} event")
                event = matches[0]
                require(event.get("reply_sha256") == reply_sha, f"{run_id} attempt {attempt}: {kind} reply digest mismatch")
                if kind == "review_recorded":
                    require(event.get("call_id") == call_id, f"{run_id} attempt {attempt}: {kind} call id mismatch")
                elif kind == "reply_available":
                    require(event.get("tool") == review["tool"] and event.get("relay_id") == reply["id"],
                            f"{run_id} attempt {attempt}: reply availability attribution mismatch")
                if kind == "review_recorded":
                    require(event.get("source_sequence") == sequence, f"{run_id} attempt {attempt}: review event sequence mismatch")
                    require(event.get("task") == review["task"] and event.get("phase") == review["phase"],
                            f"{run_id} attempt {attempt}: review event attribution mismatch")
            checked += 1
    return {"status": "PASS", "review_reply_image_event_bindings": checked}


def main() -> None:
    bindings = audit_bindings()
    result = {
        "status": "PASS",
        "baseline_auditor": "audit_replay.py (retained output checked; not rerun because its frozen code-hash manifest is checkout-line-ending-sensitive)",
        "baseline_output": "../REPLAY_AUDIT.json (preserved, PASS)",
        "additional_audit": bindings,
        "scope": "Offline integrity joins among retained review receipts, returned replies, embedded source/call metadata, returned image bytes, and host event journal. No live run or task-success claim.",
    }
    output = Path(__file__).resolve().parent / "RESULT.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
