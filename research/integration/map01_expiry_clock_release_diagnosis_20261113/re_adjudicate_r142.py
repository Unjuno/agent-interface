from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0,
    str(REPO_ROOT / "research/integration/map01_numeric_ammo_oracle_20261111"),
)
from input_boundary import audit_expiry_key_release  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: re_adjudicate_r142.py PACKET_ROOT OUTPUT.json")
    packet_root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2])
    trial = packet_root / "trials/r142_native_win32_scan_code_demo_expiry_map01"
    raw_path = trial / "expiry-boundary-key-samples.json"
    old_path = trial / "expiry-boundary-audit.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    old = json.loads(old_path.read_text(encoding="utf-8"))
    corrected = audit_expiry_key_release(raw["samples"], raw["lease_deadline_ns"])
    first_after = corrected["first_sample_fully_after_deadline"]
    result = {
        "schema": "map01-r142-corrected-adjudication-v1",
        "source_packet": packet_root.name,
        "source_files": {
            "raw": {
                "path": "trials/r142_native_win32_scan_code_demo_expiry_map01/expiry-boundary-key-samples.json",
                "sha256": sha256(raw_path),
            },
            "original_audit": {
                "path": "trials/r142_native_win32_scan_code_demo_expiry_map01/expiry-boundary-audit.json",
                "sha256": sha256(old_path),
            },
        },
        "original_audit": {
            "status": old.get("status"),
            "qpc_bracket_gap_ns": old.get("qpc_bracket_gap_ns"),
            "post_deadline_down_duration_ns": old.get(
                "post_deadline_down_duration_ns"
            ),
        },
        "corrected_audit": {
            "status": corrected["status"],
            "qpc_bracket_gap_ns": corrected["qpc_bracket_gap_ns"],
            "qpc_bracket_outer_ns": corrected["qpc_bracket_outer_ns"],
            "post_deadline_down_duration_ns": corrected[
                "post_deadline_down_duration_ns"
            ],
            "first_strictly_post_deadline_sample": (
                {
                    "monotonic_before_ns": first_after["monotonic_before_ns"],
                    "monotonic_after_ns": first_after["monotonic_after_ns"],
                    "perf_counter_start_ns": first_after[
                        "perf_counter_start_ns"
                    ],
                    "w_key_down": first_after["w_key_down"],
                }
                if first_after is not None
                else None
            ),
            "equal_deadline_rows_excluded": sum(
                row.get("monotonic_before_ns") == raw["lease_deadline_ns"]
                and row.get("monotonic_after_ns") == raw["lease_deadline_ns"]
                for row in raw["samples"]
            ),
        },
        "interpretation": (
            "Read-only re-adjudication; original R142 result and raw are unchanged. "
            "The corrected strict timing gate remains not_verified; this does not "
            "change the task-effect, recovery, horizon, or demo adjudications."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
