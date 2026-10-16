from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import sys


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(raw_path: Path, result_root: Path, out_path: Path) -> None:
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    p1, p2 = raw["p1"], raw["p2"]
    pixels = raw["independent_window_pixels"]
    p1_bytes = base64.b64decode(pixels["p1"]["base64"], validate=True)
    p2_bytes = base64.b64decode(pixels["p2"]["base64"], validate=True)
    releases = raw["fresh_control"]["result"]["execution"]["releases"]
    release_ok = bool(releases) and all(
        row.get("verified") is True and row.get("keys_down") == []
        and row.get("buttons_down") == [] for row in releases
    )
    png_rows = []
    for item in raw.get("images", []):
        path = result_root / item["path"]
        data = path.read_bytes()
        png_rows.append({"path": item["path"], "bytes_match": len(data) == item["bytes"],
                         "sha256_match": sha(data) == item["sha256"]})
    checks = {
        "candidate_pass": raw.get("decision") == "PASS_GENERATION_GUARD_REJECTED_STALE_ALIAS",
        "preconditions_all_true": all(raw.get("preconditions", {}).values()),
        "same_xid_geometry_and_exact_pixels": (
            p1["xid"] == p2["xid"]
            and p1["geometry"] == p2["geometry"]
            and pixels.get("pixel_identical") is True
            and p1_bytes == p2_bytes
            and sha(p1_bytes) == pixels["p1"]["sha256"]
            and sha(p2_bytes) == pixels["p2"]["sha256"]
        ),
        "different_process_incarnations": (
            p1["pid"] != p2["pid"]
            and p1["pid_start_ticks"] != p2["pid_start_ticks"]
            and raw["old_handle"]["owner_identity"]["pid"] == p1["pid"]
            and raw["p2_owner_identity"]["pid"] == p2["pid"]
        ),
        "stale_refusal_before_bridge_click_zero_emission_effect": (
            raw["old_guard_decisions"] == 1
            and raw["old_alias_guard"]["permitted"] is False
            and raw["old_alias_guard"]["reason"] == "PROCESS_INCARNATION_MISMATCH"
            and raw["old_alias_guard"]["bridge_click_invoked"] is False
            and raw["bridge_old_click_invocations"] == 0
            and raw["old_alias_guard"]["emissions_before"] == raw["old_alias_guard"]["emissions_after"] == 0
            and raw["old_alias_guard"]["effect_before"] == raw["old_alias_guard"]["effect_after"] == [0, 0, 0]
        ),
        "fresh_control_after_stale_refusal": (
            raw["fresh_control_attempts"] == 1
            and raw["fresh_control"]["permitted"] is True
            and raw["fresh_control"]["reason"] == "SAME_PROCESS_INCARNATION"
            and raw["fresh_control"]["result"]["status"] == "completed"
            and raw["fresh_control"]["emissions_after"] - raw["fresh_control"]["emissions_before"] == 3
            and raw["fresh_control"]["effect"] == [1, 212, 118]
        ),
        "verified_empty_release": release_ok,
        "cleanup": (
            raw.get("bridge_closed") is True
            and raw.get("p1_cleanup", {}).get("exit_observed") is True
            and raw.get("p1_cleanup", {}).get("exit_code") == 0
            and raw.get("p2_cleanup", {}).get("exit_observed") is True
            and raw.get("p2_cleanup", {}).get("exit_code") == 0
        ),
        "all_pngs_match_raw_manifest": bool(png_rows) and all(
            row["bytes_match"] and row["sha256_match"] for row in png_rows
        ),
    }
    result = {
        "audit": "PASS_SUPPLEMENTAL_RAW_AND_ARTIFACT_RECONSTRUCTION" if all(checks.values()) else "HOLD_SUPPLEMENTAL_AUDIT",
        "allocation_id": raw.get("allocation_id"),
        "raw_sha256": sha(raw_bytes),
        "checks": checks,
        "pngs": png_rows,
    }
    out_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
