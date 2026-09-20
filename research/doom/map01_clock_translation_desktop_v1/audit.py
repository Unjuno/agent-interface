#!/usr/bin/env python3
"""Independent raw-journal audit; does not import runner, server, or Lease."""
import argparse
import hashlib
import json
from pathlib import Path


NS = 1_000_000_000
EXPECTED = {"translated_live_25s": "accepted",
            "expired": "expired",
            "over_horizon_31s": "rejected",
            "delayed_750ms_with_500ms_auth": "expired"}


def read_jsonl(path):
    data = Path(path).read_bytes()
    if data and not data.endswith(b"\n"):
        raise ValueError(f"incomplete final JSONL record: {path}")
    rows = [json.loads(line) for line in data.decode("utf-8").splitlines() if line]
    return data, rows


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence", type=Path)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    root = args.evidence
    result = json.loads((root/"result.json").read_text(encoding="utf-8"))
    errors = []
    _, samples = read_jsonl(root/"samples.jsonl")
    _, controls = read_jsonl(root/"controls.jsonl")
    _, server = read_jsonl(root/"server.jsonl")
    _, host = read_jsonl(root/"host.jsonl")
    if result.get("status") != "FORMAL_COMPLETE_PENDING_INDEPENDENT_AUDIT":
        errors.append("formal_runner_not_complete")
    if len(samples) != 120:
        errors.append("sample_denominator")
    if len(controls) != 4:
        errors.append("control_denominator")
    if len(server) != 125 or len(host) != 125:
        errors.append("transport_journal_denominator")
    server_by_id = {r["request"]["request_id"]: r for r in server}
    host_by_id = {r["response"]["request_id"]: r for r in host}
    if len(server_by_id) != len(server) or len(host_by_id) != len(host):
        errors.append("duplicate_request_id")

    intervals = []
    for i, row in enumerate(samples):
        req_id = row["request"]["request_id"]
        if req_id not in server_by_id or req_id not in host_by_id:
            errors.append(f"sample_{i}_missing_transport_peer")
            continue
        if row.get("sample_index") != i or row["request"].get("sample_index") != i:
            errors.append(f"sample_{i}_order")
        server_row = server_by_id[req_id]
        host_row = host_by_id[req_id]
        response = server_row["response"]
        if response != row["response"] or response != host_row["response"]:
            errors.append(f"sample_{i}_response_mismatch")
        c2, c3 = response["container_receive_ns"], response["container_send_ns"]
        h1, h4 = row["host_send_ns"], row["host_receive_ns"]
        low, high = c3-h4, c2-h1
        if low > high or [low, high] != row.get("offset_interval_ns"):
            errors.append(f"sample_{i}_interval_reconstruction")
        if high-low > 250_000_000:
            errors.append(f"sample_{i}_interval_width")
        if row.get("rtt_ns") != h4-h1 or h4 <= h1:
            errors.append(f"sample_{i}_rtt")
        intervals.append((low, high))
        if i:
            elapsed = row["scheduled_elapsed_ns"]-samples[i-1]["scheduled_elapsed_ns"]
            if not 4_500_000_000 <= elapsed <= 5_500_000_000:
                errors.append(f"sample_{i}_cadence")
    if intervals:
        common = [max(low for low, _ in intervals), min(high for _, high in intervals)]
        if common != result.get("offset_common_intersection_ns"):
            errors.append("common_intersection_mismatch")
        if common[0] > common[1]:
            errors.append("common_intersection_empty")
        if result.get("conservative_offset_ns") != common[0]:
            errors.append("conservative_offset_not_lower_endpoint")

    control_rows = {r.get("control"): r for r in controls}
    if set(control_rows) != set(EXPECTED):
        errors.append("control_identity_set")
    for name, expected in EXPECTED.items():
        row = control_rows.get(name)
        if not row:
            continue
        response = row["response"]
        if response.get("decision") != expected:
            errors.append(f"{name}_validator_decision")
        if name == "translated_live_25s" and response.get("remaining_ns", 0) <= 0:
            errors.append("live_lease_not_live")
        if response.get("decision") == "accepted":
            remaining_container = response["lease_deadline_ns"]-response["remaining_sample_ns"]
            remaining_host_min = row["host_deadline_ns"]-response["remaining_sample_ns"]+result["conservative_offset_ns"]
            if remaining_container > remaining_host_min:
                errors.append(f"{name}_authority_extended")
            if remaining_container != response.get("remaining_ns"):
                errors.append(f"{name}_remaining_reconstruction")
        if name == "delayed_750ms_with_500ms_auth":
            elapsed = response.get("validation_start_ns", 0)-response.get("container_receive_ns", 0)
            if elapsed < 750_000_000:
                errors.append("delayed_control_delay_missing")

    if result.get("lease_sha256") != sha(args.repo/"research/live_control/lease.py"):
        errors.append("lease_source_hash")
    if result.get("exchange_sha256") != sha(args.repo/"research/live_control/unix_json_deadline.py"):
        errors.append("exchange_source_hash")
    if result.get("lease_sha256") != "E71F9850D3999A31FCB86C00F9EF7A8BA19BAE8D3A8BDC11BF7BD620817A535F":
        errors.append("lease_frozen_hash")
    if result.get("exchange_sha256") != "DECB19099C686EE494FE307C3BF411E61C59E05470319AB80159147D2BD73DE3":
        errors.append("exchange_frozen_hash")
    source_dir = args.repo/"research/doom/map01_clock_translation_desktop_v1"
    manifest_path = source_dir/"SOURCE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual_allocation_hashes = {name: sha(source_dir/name)
                                for name in manifest["allocation_sources"]}
    if actual_allocation_hashes != manifest["allocation_sources"]:
        errors.append("allocation_source_manifest")
    if result.get("allocation_source_hashes") != manifest["allocation_sources"]:
        errors.append("runner_allocation_hash_receipt")
    if result.get("source_manifest_sha256") != sha(manifest_path):
        errors.append("source_manifest_hash")
    if result.get("container_exit_code") != "0":
        errors.append("container_terminal_exit")
    if not result.get("container_terminal_receipt", "").startswith("exited 0"):
        errors.append("container_cleanup_receipt")
    decision = ("PASS_DOCKERDESKTOP_WSL_LEASE_TRANSLATION_SCOPED"
                if not errors else "FAIL_OR_HOLD_INDEPENDENT_AUDIT")
    audit = {"schema": "issue3886_desktop_wsl_clock_audit_v1",
             "decision": decision, "errors": errors,
             "samples": len(samples), "controls": len(controls),
             "host_transport_records": len(host),
             "container_transport_records": len(server),
             "offset_intersection_ns": result.get("offset_common_intersection_ns"),
             "max_interval_width_ns": max((hi-lo for lo, hi in intervals), default=None),
             "source_sha256": {"lease": sha(args.repo/"research/live_control/lease.py"),
                               "unix_json_deadline": sha(args.repo/"research/live_control/unix_json_deadline.py"),
                               "manifest": sha(manifest_path),
                               "allocation": actual_allocation_hashes}}
    args.out.write_text(json.dumps(audit, indent=2, sort_keys=True)+"\n",
                        encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
