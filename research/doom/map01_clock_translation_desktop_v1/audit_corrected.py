#!/usr/bin/env python3
"""Independent post-hoc correction auditor; never imports the formal runner."""
import argparse
import hashlib
import json
from pathlib import Path


EXPECTED = {"translated_live_25s": "accepted", "expired": "expired",
            "over_horizon_31s": "rejected",
            "delayed_750ms_with_500ms_auth": "expired"}


def read_rows(path):
    raw = Path(path).read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise ValueError(f"truncated JSONL: {path}")
    return [json.loads(x) for x in raw.decode().splitlines() if x]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence", type=Path)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.evidence
    result = json.loads((root/"result.json").read_text(encoding="utf-8"))
    samples = read_rows(root/"samples.jsonl")
    controls = read_rows(root/"controls.jsonl")
    host = read_rows(root/"host.jsonl")
    server = read_rows(root/"server.jsonl")
    errors = []
    if result.get("status") != "FORMAL_COMPLETE_PENDING_INDEPENDENT_AUDIT":
        errors.append("runner_not_complete")
    if len(samples) != 120 or len(controls) != 4 or len(host) != 125 or len(server) != 125:
        errors.append("denominator")
    host_ids = {row["response"]["request_id"]: row for row in host}
    server_ids = {row["request"]["request_id"]: row for row in server}
    if len(host_ids) != 125 or len(server_ids) != 125:
        errors.append("request_id_uniqueness")

    intervals = []
    for index, row in enumerate(samples):
        request_id = row["request"]["request_id"]
        h1, h4 = row["host_send_ns"], row["host_receive_ns"]
        response = row["response"]
        c2, c3 = response["container_receive_ns"], response["container_send_ns"]
        lo, hi = c3-h4, c2-h1
        if row.get("sample_index") != index or row["request"].get("sample_index") != index:
            errors.append(f"sample_{index}_order")
        if row.get("lower_offset_ns") != lo or row.get("upper_offset_ns") != hi:
            errors.append(f"sample_{index}_interval")
        if lo > hi or hi-lo > 250_000_000:
            errors.append(f"sample_{index}_bound")
        if row.get("rtt_ns") != h4-h1:
            errors.append(f"sample_{index}_rtt")
        if request_id not in host_ids or request_id not in server_ids:
            errors.append(f"sample_{index}_transport_record")
        else:
            if host_ids[request_id]["response"] != response or server_ids[request_id]["response"] != response:
                errors.append(f"sample_{index}_response_integrity")
        intervals.append((lo, hi))
        if index:
            delta = row["scheduled_elapsed_ns"]-samples[index-1]["scheduled_elapsed_ns"]
            if not 4_500_000_000 <= delta <= 5_500_000_000:
                errors.append(f"sample_{index}_cadence")
    intersection = [max(x[0] for x in intervals), min(x[1] for x in intervals)] if intervals else None
    if intersection != result.get("offset_common_intersection_ns"):
        errors.append("intersection")
    if not intersection or intersection[0] > intersection[1]:
        errors.append("intersection_empty")
    if intersection and result.get("conservative_offset_ns") != intersection[0]:
        errors.append("translation_not_lower_endpoint")

    controls_by_name = {row.get("control"): row for row in controls}
    if set(controls_by_name) != set(EXPECTED):
        errors.append("control_set")
    for name, expected in EXPECTED.items():
        row = controls_by_name.get(name)
        if not row:
            continue
        response = row["response"]
        if response.get("decision") != expected:
            errors.append(f"{name}_decision")
        request_id = row["request"]["request_id"]
        if request_id not in server_ids or server_ids[request_id]["response"] != response:
            errors.append(f"{name}_container_journal")
        if response.get("decision") == "accepted":
            c_sample = response["remaining_sample_ns"]
            r_container = row["deadline_ns"]-c_sample
            r_host_min = row["host_deadline_ns"]-c_sample+result["conservative_offset_ns"]
            if r_container != response.get("remaining_ns") or r_container > r_host_min:
                errors.append(f"{name}_authority")
    delayed = controls_by_name.get("delayed_750ms_with_500ms_auth")
    if delayed:
        response = delayed["response"]
        if response.get("validation_start_ns", 0)-response.get("container_receive_ns", 0) < 750_000_000:
            errors.append("delay_not_applied")

    manifest_path = args.repo/"research/doom/map01_clock_translation_desktop_v1/SOURCE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_dir = manifest_path.parent
    frozen_hashes = {name: sha(source_dir/name) for name in manifest["allocation_sources"]}
    if frozen_hashes != manifest["allocation_sources"]:
        errors.append("frozen_source_hashes")
    if result.get("allocation_source_hashes") != manifest["allocation_sources"]:
        errors.append("result_source_receipt")
    if result.get("source_manifest_sha256") != sha(manifest_path):
        errors.append("manifest_hash")
    production = {"lease": sha(args.repo/"research/live_control/lease.py"),
                  "unix_json_deadline": sha(args.repo/"research/live_control/unix_json_deadline.py")}
    if production["lease"] != manifest["production_sources"]["research/live_control/lease.py"]:
        errors.append("lease_production_hash")
    if production["unix_json_deadline"] != manifest["production_sources"]["research/live_control/unix_json_deadline.py"]:
        errors.append("json_production_hash")
    if result.get("container_exit_code") != "0" or result.get("container_terminal_receipt") != "exited 0":
        errors.append("terminal_receipt")
    decision = "PASS_DOCKERDESKTOP_WSL_LEASE_TRANSLATION_SCOPED" if not errors else "FAIL_OR_HOLD_INDEPENDENT_AUDIT"
    audit = {"schema": "issue3886_desktop_wsl_clock_audit_corrected_v1",
             "decision": decision, "errors": errors,
             "samples": len(samples), "controls": len(controls),
             "host_records": len(host), "container_records": len(server),
             "offset_intersection_ns": intersection,
             "max_interval_width_ns": max((b-a for a, b in intervals), default=None),
             "source_hashes": {"manifest": sha(manifest_path), **frozen_hashes,
                               "audit_corrected.py": sha(Path(__file__)), **production}}
    args.out.write_text(json.dumps(audit, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
