from __future__ import annotations

import hashlib
import base64
import io
import json
import lzma
import subprocess
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "candidate.raw.json"
OUT = HERE / "audit.raw.json"
PREFIX = "research/integration/x11_reconnect_key_state_2107_v1/"


def independent_reconstruction(root: Path, commit: str, freeze: dict) -> dict:
    meta = json.loads(subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:{PREFIX}EVIDENCE_BASE64.json"]))
    if meta.get("archive_sha256") != freeze["archive_sha256"] or meta.get("archive_bytes") != freeze["archive_bytes"]:
        raise ValueError("INDEPENDENT_FROZEN_ARCHIVE_METADATA_MISMATCH")
    encoded = []
    for part in meta["parts"]:
        source = subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:{PREFIX}{part['path']}"]).decode("ascii").strip()
        if freeze["archive_parts"].get(part["path"]) != part["sha256"] or len(source) != part["chars"] or hashlib.sha256(source.encode("ascii")).hexdigest() != part["sha256"]:
            raise ValueError("INDEPENDENT_ARCHIVE_PART_INTEGRITY")
        encoded.append(source)
    archive = base64.b64decode("".join(encoded), validate=True)
    if len(archive) != meta["archive_bytes"] or hashlib.sha256(archive).hexdigest() != meta["archive_sha256"]:
        raise ValueError("INDEPENDENT_ARCHIVE_HASH_MISMATCH")
    tar = tarfile.open(fileobj=io.BytesIO(lzma.decompress(archive)), mode="r:")
    members = {m.name: m for m in tar.getmembers() if m.isfile()}
    cases = []
    for name, member in members.items():
        if "/formal_v2/" in name and name.endswith("/case.json"):
            cases.append((name, json.loads(tar.extractfile(member).read())))
    chosen = [(name, obj) for name, obj in cases
              if obj.get("scenario") in ("DISCONNECT_PRESS", "DISCONNECT_RELEASE")
              and obj.get("policy") == "REBOOTSTRAP_ON_RECONNECT"]
    summaries = []
    edge_patterns = ("causal", "parent", "message_id", "message-id", "send_id", "receive_id", "send-id", "receive-id")
    for name, obj in chosen:
        folder = name.rsplit("/", 1)[0]
        observed = [json.loads(line) for line in tar.extractfile(members[folder + "/observer2.jsonl"]).read().splitlines() if line]
        app = [json.loads(line) for line in tar.extractfile(members[folder + "/app/app_events.jsonl"]).read().splitlines() if line]
        all_events = observed + app
        field_names = {key for event in all_events for key in event}
        explicit_fields = sorted(k for k in field_names if any(pat in k.lower() for pat in edge_patterns))
        summaries.append({
            "case_path": name,
            "scenario": obj.get("scenario"),
            "rep": obj.get("rep"),
            "case_epoch": obj.get("epoch"),
            "bootstrap_epoch": (obj.get("bootstrap_packet") or {}).get("epoch"),
            "bootstrap_epoch_matches": (obj.get("bootstrap_packet") or {}).get("epoch") == obj.get("epoch"),
            "observer_event_count": len(observed),
            "observer_raw_matches_aggregate": observed == obj.get("observer2_events"),
            "observer_event_epochs_match": all(event.get("epoch") == obj.get("epoch") for event in observed),
            "app_event_count": len(app),
            "app_raw_matches_aggregate": app == obj.get("app_events"),
            "event_fields": sorted(field_names),
            "explicit_causal_edge_fields": explicit_fields,
            "monotonic_timestamps_both_streams": all("mono_ns" in event for event in all_events),
            "final_value": obj.get("final_value"),
            "final_neutral": obj.get("final_neutral"),
        })
    complete = all(s["observer_raw_matches_aggregate"] and s["app_raw_matches_aggregate"] for s in summaries)
    epochs_ok = all(s["bootstrap_epoch_matches"] and s["observer_event_epochs_match"] for s in summaries)
    edge_rows = sum(bool(s["explicit_causal_edge_fields"]) for s in summaries)
    obs_source = subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:{PREFIX}observer.py"])
    app_source = subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:{PREFIX}app.py"])
    if len(summaries) == 4 and complete and epochs_ok and edge_rows == 0:
        disposition = "HOLD_CAUSAL_EDGE_PROVENANCE_MISSING" if hashlib.sha256(obs_source).hexdigest() == freeze["source_hashes"]["observer.py"] and hashlib.sha256(app_source).hexdigest() == freeze["source_hashes"]["app.py"] and len(members) == freeze["expanded_file_count"] and len(cases) == 24 else "STOP_TRACE_INTEGRITY_OR_INVENTORY"
    elif len(summaries) == 0:
        disposition = "HOLD_NO_ELIGIBLE_TRACE"
    elif len(summaries) == 4 and complete and epochs_ok and edge_rows == 4:
        disposition = "PASS_TRACE_CUT_APPLICABILITY"
    else:
        disposition = "STOP_TRACE_INTEGRITY_OR_INVENTORY"
    return {
        "archive_sha256": hashlib.sha256(archive).hexdigest(), "archive_bytes": len(archive),
        "expanded_file_count": len(members), "formal_case_count": len(cases),
        "frozen_inventory_ok": len(members) == freeze["expanded_file_count"] and len(cases) == 24 and len(summaries) == freeze["selected_cases"]["expected_rows"],
        "selected_positive_case_count": len(summaries), "selected_rows": summaries,
        "raw_aggregates_match": complete, "bootstrap_epochs_match": epochs_ok,
        "explicit_cross_source_edge_rows": edge_rows,
        "observer_source_sha256": hashlib.sha256(obs_source).hexdigest(),
        "app_source_sha256": hashlib.sha256(app_source).hexdigest(),
        "frozen_source_hashes_match": hashlib.sha256(obs_source).hexdigest() == freeze["source_hashes"]["observer.py"] and hashlib.sha256(app_source).hexdigest() == freeze["source_hashes"]["app.py"],
        "observer_uses_one_display_for_bootstrap_and_events": obs_source.count(b"display.Display()") == 1 and obs_source.index(b"query_keymap()") < obs_source.index(b"while True:") and b"d.pending_events()" in obs_source,
        "app_emits_monotonic_state_and_event_records": b"time.monotonic_ns()" in app_source,
        "disposition": disposition,
    }


def main() -> None:
    if OUT.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    changed_sources = [name for name, expected_hash in freeze["analysis_sources_sha256"].items()
                       if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected_hash]
    raw = RAW.read_bytes()
    recorded = json.loads(raw)
    # Rebuild from frozen Git blobs; do not trust the candidate's aggregate rows.
    expected = independent_reconstruction(root, freeze["source_commit"], freeze)
    errors = [f"{name}:FROZEN_ANALYSIS_SOURCE_CHANGED" for name in changed_sources]
    for key in ["archive_sha256", "archive_bytes", "expanded_file_count", "formal_case_count",
                "selected_positive_case_count", "selected_rows", "raw_aggregates_match",
                "frozen_inventory_ok",
                "bootstrap_epochs_match", "explicit_cross_source_edge_rows",
                "observer_source_sha256", "app_source_sha256",
                "frozen_source_hashes_match",
                "observer_uses_one_display_for_bootstrap_and_events",
                "app_emits_monotonic_state_and_event_records", "disposition"]:
        if recorded.get(key) != expected.get(key):
            errors.append(f"{key}:INDEPENDENT_RECONSTRUCTION_MISMATCH")
    selected = expected["selected_rows"]
    if len(selected) != 4:
        errors.append("SELECTED_ROW_COUNT_NOT_FOUR")
    if expected["disposition"] != "HOLD_CAUSAL_EDGE_PROVENANCE_MISSING":
        errors.append("EXPECTED_CAUSAL_PROVENANCE_HOLD_NOT_OBSERVED")
    if any(r["explicit_causal_edge_fields"] for r in selected):
        errors.append("UNEXPECTED_EXPLICIT_EDGE_FIELD")
    if not all(r["bootstrap_epoch_matches"] and r["observer_event_epochs_match"] for r in selected):
        errors.append("BOOTSTRAP_EPOCH_BINDING_FAILED")
    status = "PASS_AUDIT_HOLD_CAUSAL_EDGE_PROVENANCE_MISSING" if not errors else "FAIL_AUDIT_INTEGRITY"
    result = {"schema": "blackstart-trace-applicability-independent-audit-v1", "status": status,
              "candidate_sha256": hashlib.sha256(raw).hexdigest(), "selected_rows": len(selected),
              "cross_source_edge_rows": expected["explicit_cross_source_edge_rows"],
              "errors": errors}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
