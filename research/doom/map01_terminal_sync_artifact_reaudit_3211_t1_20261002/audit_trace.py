from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from collections import Counter


TARGET = (
    "results-local/doom/map01-terminal-sync-diagnostic-3211-04/"
    "pair-01/coast_control/session-events.jsonl"
)
MANIFEST = "evidence-manifest/result-sha256sums.txt"
PREFIX = "results-local/doom/map01-terminal-sync-diagnostic-3211-04/pair-01/"


def parse_object_stream(raw: bytes) -> tuple[list[dict], str]:
    text = raw.decode("utf-8")
    decoder = json.JSONDecoder()
    rows: list[dict] = []
    offset = 0
    while offset < len(text):
        if text.startswith("\\n", offset):
            offset += 2
            continue
        if text[offset] in "\r\n \t":
            offset += 1
            continue
        value, end = decoder.raw_decode(text, offset)
        if not isinstance(value, dict):
            raise ValueError(f"event row is not an object at character {offset}")
        rows.append(value)
        offset = end
    if not rows:
        raise ValueError("event stream contains no objects")
    normal_jsonl = True
    for line in raw.splitlines():
        if not line:
            continue
        try:
            value = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError):
            normal_jsonl = False
            break
        if not isinstance(value, dict):
            normal_jsonl = False
            break
    return rows, "JSONL" if normal_jsonl else "OBJECT_STREAM_WITH_ESCAPED_NEWLINE_DELIMITERS"


def _manifest_sha(manifest: bytes, member: str) -> str:
    matches: list[str] = []
    for raw_line in manifest.decode("utf-8").splitlines():
        fields = raw_line.split(None, 1)
        if len(fields) == 2 and fields[1].lstrip("*") == member:
            matches.append(fields[0])
    if len(matches) != 1:
        raise ValueError(f"expected one manifest entry for {member}, got {len(matches)}")
    return matches[0]


def audit(archive: str) -> dict:
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if names.count(TARGET) != 1 or names.count(MANIFEST) != 1:
            raise ValueError("target trace or manifest is missing/duplicated")
        raw = bundle.read(TARGET)
        manifest = bundle.read(MANIFEST)
        trace_members = sorted(
            name for name in names
            if name.startswith(PREFIX) and name.endswith("/session-events.jsonl")
        )
    expected_sha = _manifest_sha(manifest, TARGET)
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != expected_sha:
        raise ValueError("session trace SHA-256 does not match artifact manifest")
    rows, trace_format = parse_object_stream(raw)
    terminals = [row for row in rows if row.get("event") == "terminal"]
    coast_terminals = [row for row in terminals if "coast_control" in str(row.get("id", ""))]
    recovery_terminals = [row for row in terminals if "recovery" in str(row.get("id", "")).lower()]
    release_verified = all(
        isinstance(row.get("release"), dict) and row["release"].get("verified") is True
        for row in coast_terminals
    )
    recovery_stream_present = any("recovery" in name.lower() for name in trace_members)
    scientific_classification = (
        "RECOVERY_TERMINAL_TRACE_PRESENT"
        if recovery_stream_present and recovery_terminals
        else "RECOVERY_TRACE_PRESENT_WITHOUT_MATCHING_TERMINAL"
        if recovery_stream_present
        else "RECOVERY_TERMINAL_NOT_IDENTIFIABLE"
    )
    return {
        "schema": "map01-terminal-sync-artifact-reaudit-v1",
        "artifact_id": 10592018768,
        "workflow_run_id": 35470604368,
        "target_member": TARGET,
        "manifest_sha256": expected_sha,
        "actual_sha256": actual_sha,
        "byte_count": len(raw),
        "trace_member_count": len(trace_members),
        "trace_members": trace_members,
        "parsed_object_count": len(rows),
        "event_counts": dict(sorted(Counter(row.get("event", "<missing>") for row in rows).items())),
        "trace_format": trace_format,
        "terminal_rows": [
            {
                "id": row.get("id"),
                "status": row.get("status"),
                "terminal_ns": row.get("terminal_ns"),
                "release_verified": (row.get("release") or {}).get("verified") is True,
            }
            for row in terminals
        ],
        "coast_terminal_count": len(coast_terminals),
        "coast_terminals_release_verified": release_verified,
        "recovery_terminal_count": len(recovery_terminals),
        "recovery_trace_member_present": recovery_stream_present,
        "audit_decision": "PASS_RAW_ARTIFACT_INTEGRITY_PARTIAL_SCOPE",
        "scientific_classification": scientific_classification,
        "claim_boundary": (
            "The archived coast trace is hash-verified and structurally parseable. "
            "No recovery-arm trace is present in this artifact; this does not prove "
            "whether a recovery terminal was emitted outside the retained artifact."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    args = parser.parse_args()
    result = audit(args.artifact)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
