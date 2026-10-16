#!/usr/bin/env python3
"""Audit the retained V39 decision-5 observations against planner protocol.

Usage: python audit.py PATH/TO/map01-v39-coast-liveness-live-01
Requires Pillow for decoding retained PNGs.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image

SEQUENCES = (154, 200, 204)
TURN_ID = "01a0a389-810e-7bf3-894e-7a88827c1d49"

def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

def main(root: Path) -> None:
    root = root.resolve()
    manifest = json.loads((root / "retention-manifest.json").read_text(encoding="utf-8"))
    require(manifest.get("schema") == "map01-v39-first-outcome-retention-v1", "unexpected retention manifest schema")
    require(manifest.get("allocation_id") == "map01-v39-coast-liveness-live-01", "wrong allocation")
    entries = {item["path"]: item for item in manifest["files"]}

    def verify_retained(rel: str) -> bytes:
        require(rel in entries, f"{rel} is absent from retention manifest")
        data = (root / rel).read_bytes()
        item = entries[rel]
        require(len(data) == item["bytes"], f"retained byte length mismatch: {rel}")
        require(sha256(data) == item["sha256"], f"retained SHA-256 mismatch: {rel}")
        return data

    events_bytes = verify_retained("runtime/events.jsonl")
    protocol_bytes = verify_retained("planner-protocol.jsonl")
    report_bytes = verify_retained("report.json")
    events = [json.loads(line) for line in events_bytes.decode("utf-8").splitlines() if line]
    protocol = [json.loads(line) for line in protocol_bytes.decode("utf-8").splitlines() if line]
    report = json.loads(report_bytes)

    indexed: dict[int, dict[str, dict]] = {}
    for seq in SEQUENCES:
        matches = [e for e in events if e.get("sequence") == seq and e.get("event") in {"typed_observation", "observation"}]
        kinds = {e["event"]: e for e in matches}
        require(set(kinds) == {"typed_observation", "observation"}, f"sequence {seq}: expected one typed and one image observation")
        typed, visual = kinds["typed_observation"], kinds["observation"]
        require(visual.get("exact") is True, f"sequence {seq}: image observation is not exact")
        require(typed.get("frame_rgb_sha256") == visual.get("frame_rgb_sha256"), f"sequence {seq}: event RGB hashes differ")
        require(typed.get("capture_ns") == visual.get("capture_ns"), f"sequence {seq}: capture timestamps differ")
        require(typed.get("id") == visual.get("id") and typed.get("step") == visual.get("step"), f"sequence {seq}: typed/image identities differ")
        require(typed.get("grants_input_authority") is False, f"sequence {seq}: observation unexpectedly grants input authority")
        img_rel = f"runtime/{seq}.png"
        png = verify_retained(img_rel)
        with Image.open(root / img_rel) as im:
            rgb = im.convert("RGB")
            require(list(rgb.size) == typed.get("frame_size", [1280, 800]), f"sequence {seq}: PNG dimensions mismatch")
            require(sha256(rgb.tobytes()) == typed["frame_rgb_sha256"], f"sequence {seq}: PNG pixels do not match event RGB hash")
        indexed[seq] = kinds

    starts = []
    for i, row in enumerate(protocol):
        msg = row.get("message", {})
        if row.get("direction") != "sent" or msg.get("method") != "turn/start":
            continue
        params = msg.get("params", {})
        inputs = params.get("input", [])
        prompt = "\n".join(x.get("text", "") for x in inputs if x.get("type") == "text")
        image_paths = [x.get("path", "") for x in inputs if x.get("type") == "localImage"]
        if "Current locally verified health: 61." in prompt and "Current locally verified ammo: 40." in prompt and any("decision-5\\temporal-sheet.png" in p or "decision-5/temporal-sheet.png" in p for p in image_paths):
            starts.append((i, row))
    require(len(starts) == 1, "could not uniquely identify decision-5 turn/start")
    start_i, start_row = starts[0]
    thread_id = start_row["message"]["params"]["threadId"]
    start_ns = start_row["observed_ns"]

    started = [(i, r) for i, r in enumerate(protocol) if r.get("message", {}).get("method") == "turn/started" and r.get("message", {}).get("params", {}).get("turn", {}).get("id") == TURN_ID]
    interrupts = [(i, r) for i, r in enumerate(protocol) if r.get("direction") == "sent" and r.get("message", {}).get("method") == "turn/interrupt" and r.get("message", {}).get("params", {}).get("turnId") == TURN_ID]
    completions = [(i, r) for i, r in enumerate(protocol) if r.get("message", {}).get("method") == "turn/completed" and r.get("message", {}).get("params", {}).get("turn", {}).get("id") == TURN_ID]
    require(len(started) == len(interrupts) == len(completions) == 1, "decision-5 turn lifecycle is not unique")
    started_i, started_row = started[0]
    interrupt_i, interrupt_row = interrupts[0]
    completed_i, completed_row = completions[0]
    require(started_i > start_i and started_row["observed_ns"] >= start_ns, "turn start ordering mismatch")
    require(started_row["message"]["params"]["threadId"] == thread_id, "turn belongs to another thread")
    require(interrupt_i < completed_i and completed_i > started_i, "turn terminal ordering mismatch")
    require(completed_row["message"]["params"]["turn"]["status"] == "interrupted", "turn did not complete as interrupted")
    interrupt_ns = interrupt_row["observed_ns"]
    for seq in (200, 204):
        capture_ns = indexed[seq]["typed_observation"]["capture_ns"]
        require(start_ns < capture_ns < interrupt_ns, f"sequence {seq} was not captured during the pending turn")

    user_items = []
    steer_rows = []
    for i, row in enumerate(protocol):
        msg = row.get("message", {})
        params = msg.get("params", {})
        if params.get("turnId") != TURN_ID:
            continue
        if msg.get("method") == "item/started" and params.get("item", {}).get("type") == "userMessage":
            user_items.append((i, params["item"]))
        if msg.get("method") in {"turn/steer", "turn/steer/start"}:
            steer_rows.append((i, msg.get("method")))
    require(len(user_items) == 1, f"expected only original user message, found {len(user_items)}")
    require(not steer_rows, f"unexpected steer event(s): {steer_rows}")

    decisions = [d for d in report.get("decisions", []) if d.get("iteration") == 5]
    require(len(decisions) == 1, "report does not uniquely identify decision 5")
    decision = decisions[0]
    require(decision.get("planner_turn_id") == TURN_ID, "report turn id differs from protocol")
    require(decision.get("planner_turn_status") == "interrupted" and decision.get("planner_answer_eligible") is False, "report does not mark the decision-5 answer ineligible")

    result = {
        "status": "PASS",
        "allocation_id": manifest["allocation_id"],
        "decision": 5,
        "turn_id": TURN_ID,
        "observations": {str(seq): {"step": indexed[seq]["typed_observation"]["step"], "health": indexed[seq]["typed_observation"]["signals"]["health"]["value"], "ammo": indexed[seq]["typed_observation"]["signals"]["ammo"]["value"], "capture_ns": indexed[seq]["typed_observation"]["capture_ns"], "rgb_sha256": indexed[seq]["typed_observation"]["frame_rgb_sha256"], "exact_image_join": True} for seq in SEQUENCES},
        "pending_turn_observations": [200, 204],
        "protocol": {"single_original_user_message": True, "steer_events": 0, "terminal_status": "interrupted", "answer_eligible": False},
        "limit": "This retrospective trace proves image-backed observations and protocol ordering only. It cannot establish what an uninterrupted natural answer would have selected or whether any live-game gate is satisfied."
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]))



