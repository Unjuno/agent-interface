"""Independent raw/result audit for one Docker Desktop construction result."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def audit(root: Path, repo: Path) -> dict:
    raw_bytes = (root / "raw.jsonl").read_bytes()
    result_bytes = (root / "result.json").read_bytes()
    manifest = {}
    for line in (root / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        manifest[name] = digest
    need(manifest.get("raw.jsonl") == sha256(raw_bytes), "raw manifest hash")
    need(manifest.get("result.json") == sha256(result_bytes), "result manifest hash")
    result = json.loads(result_bytes)
    rows = [json.loads(line) for line in raw_bytes.splitlines()]
    clocks = [row for row in rows if row.get("kind") == "clock"]
    lease_rows = [row for row in rows if row.get("kind") == "lease"]
    need(len(lease_rows) == 4, "lease-control row count")
    lease_ids = [row.get("id") for row in lease_rows]
    need(len(lease_ids) == len(set(lease_ids)), "duplicate lease-control id")
    controls = {row["id"]: row for row in lease_rows}
    need(result.get("classification") == "CONSTRUCTION_ONLY_DOCKER_DESKTOP", "scope label")
    need(result.get("clock_samples") == len(clocks) == 41, "clock denominator")
    need([row.get("i") for row in clocks] == list(range(41)), "ordered unique clock indices")
    expected_clock_bounds = {
        "min_lower_ns": min(row["offset_lower_ns"] for row in clocks),
        "max_lower_ns": max(row["offset_lower_ns"] for row in clocks),
        "min_upper_ns": min(row["offset_upper_ns"] for row in clocks),
        "max_upper_ns": max(row["offset_upper_ns"] for row in clocks),
        "max_bound_width_ns": max(row["bound_width_ns"] for row in clocks),
        "median_roundtrip_ns": sorted(row["roundtrip_ns"] for row in clocks)[len(clocks)//2],
    }
    need(result.get("clock_bounds") == expected_clock_bounds, "clock summary/raw agreement")

    for row in clocks:
        low, high = row["offset_lower_ns"], row["offset_upper_ns"]
        need(type(low) is int and type(high) is int and low <= high, "finite ordered interval")
        need(row["roundtrip_ns"] == row["h_recv_ns"] - row["h_send_ns"], "RTT equation")
        need(row["offset_lower_ns"] == row["sent_ns"] - row["h_recv_ns"], "lower-bound equation")
        need(row["offset_upper_ns"] == row["received_ns"] - row["h_send_ns"], "upper-bound equation")

    need(set(controls) == {"live-25s", "expired", "over-30s", "delayed-under-20s"}, "control set")
    summary_controls = result.get("controls")
    need(type(summary_controls) is list and len(summary_controls) == len(controls),
         "control summary denominator")
    for summary in summary_controls:
        control_id = summary.get("id") if type(summary) is dict else None
        need(control_id in controls, "control summary identity")
        raw_control = {key: value for key, value in controls[control_id].items() if key != "kind"}
        need(summary == raw_control, f"control summary/raw agreement: {control_id}")
    need({row.get("id") for row in summary_controls} == set(controls),
         "control summary unique identities")
    live, expired, over, delayed = (controls[key] for key in
                                   ("live-25s", "expired", "over-30s", "delayed-under-20s"))
    need(live["outcome"] == "accepted" and live["container_request_sent"] is True, "live lease")
    need(20_000_000_000 <= live["container_remaining_at_receive_ns"] <= 30_000_000_000,
         "live lease admission horizon")
    need(live["container_remaining_at_receive_ns"] <= live["host_remaining_at_send_ns"],
         "translation cannot increase remaining host authority")
    need(live["container_deadline_ns"] == live["host_deadline_ns"] + live["offset_lower_ns"],
         "conservative translation")
    need(expired["outcome"] == "expired", "expired control")
    need(over["outcome"] == "rejected_horizon", "over-horizon control")
    need(delayed["outcome"] == "host_fail_closed_insufficient_remaining" and
         delayed["container_request_sent"] is False and
         delayed["host_remaining_at_send_ns"] < 20_000_000_000, "delayed fail-closed")

    worker = repo / "research/doom/map01_model_loop_finite_v4/dockerdesktop_probe/worker.py"
    lease = repo / "research/live_control/lease.py"
    need(sha256(worker.read_bytes()) == result["worker_sha256"], "worker source hash")
    need(sha256(lease.read_bytes()) == result["lease_source_sha256"], "Lease source hash")
    process_exit = result.get("container_exit_code")
    disposition = ("HOLD_CONTAINER_EXIT_UNRECORDED" if process_exit is None else
                   "PASS_CONSTRUCTION_SCOPED" if type(process_exit) is int and process_exit == 0 else
                   "FAIL_CONTAINER_NONZERO_EXIT" if type(process_exit) is int else
                   "FAIL_CONTAINER_EXIT_CODE_INVALID")
    checks = {}
    for name, payload in (("raw.jsonl", raw_bytes), ("result.json", result_bytes)):
        checks[name] = sha256(payload)
    return {"disposition": disposition,
            "semantic_disposition": "PASS_CONTROLS_AND_CLOCKS_SCOPED",
            "container_exit_code": process_exit,
            "clock_rows": len(clocks), "lease_controls": sorted(controls),
            "errors": [], "sha256": checks}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.out.resolve(), args.repo.resolve())
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (args.out / "audit-followup.json").write_text(payload)
    files = [args.out / name for name in
             ("raw.jsonl", "result.json", "audit.json", "audit-followup.json")]
    (args.out / "SHA256SUMS").write_text("".join(
        f"{sha256(path.read_bytes())}  {path.name}\n" for path in files))
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
