"""Bounded host driver for the Docker Desktop construction-only probe."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    repo = args.repo.resolve()
    script = repo / "research/doom/map01_model_loop_finite_v4/dockerdesktop_probe/worker.py"
    lease = repo / "research/live_control/lease.py"
    worker_hash, lease_hash = sha256(script), sha256(lease)
    docker = ["docker", "run", "--rm", "-i", "--network", "none", "--read-only",
              "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
              "--mount", f"type=bind,source={repo},target=/repo,readonly",
              "--workdir", "/repo",
              "--env", "PYTHONPATH=/repo/research/live_control", args.image,
              "python", "-u", "/repo/research/doom/map01_model_loop_finite_v4/dockerdesktop_probe/worker.py"]
    proc = subprocess.Popen(docker, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    raw: list[dict] = []

    def exchange(payload: dict) -> tuple[int, int, dict]:
        assert proc.stdin and proc.stdout
        before = time.perf_counter_ns()
        proc.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        after = time.perf_counter_ns()
        if not line:
            raise RuntimeError("container worker exited without a response")
        return before, after, json.loads(line)

    samples = []
    try:
        # A small spread over two seconds samples startup and short-term drift.
        for idx in range(41):
            h1, h4, row = exchange({"op": "clock", "id": f"clock-{idx:02d}"})
            lower, upper = row["sent_ns"] - h4, row["received_ns"] - h1
            sample = {"i": idx, "h_send_ns": h1, **row, "h_recv_ns": h4,
                      "offset_lower_ns": lower, "offset_upper_ns": upper,
                      "roundtrip_ns": h4 - h1,
                      "bound_width_ns": upper - lower}
            samples.append(sample)
            raw.append({"kind": "clock", **sample})
            if idx in {9, 19, 29}:
                time.sleep(0.25)

        # Conservative mapping uses the lowest observed container-minus-host offset.
        offset_lower = min(row["offset_lower_ns"] for row in samples)
        controls = []

        def lease_control(name: str, host_deadline: int, delay_s: float = 0.0) -> None:
            if delay_s:
                time.sleep(delay_s)
            send_ns = time.perf_counter_ns()
            host_remaining = host_deadline - send_ns
            if name == "delayed-under-20s" and host_remaining < 20_000_000_000:
                result = {"id": name, "host_send_ns": send_ns,
                          "host_deadline_ns": host_deadline,
                          "host_remaining_at_send_ns": host_remaining,
                          "outcome": "host_fail_closed_insufficient_remaining",
                          "container_request_sent": False}
                controls.append(result)
                raw.append({"kind": "lease", **result})
                return
            # Mapping via the conservative lower offset cannot add host authority.
            translated = host_deadline + offset_lower
            h1, h4, row = exchange({"op": "lease", "id": name,
                                    "deadline_ns": translated})
            result = {"id": name, "host_now_ns": h1,
                      "host_deadline_ns": host_deadline,
                      "container_deadline_ns": translated,
                      "offset_lower_ns": offset_lower,
                      "host_remaining_at_send_ns": host_deadline - h1,
                      "container_request_sent": True,
                      "container_remaining_at_receive_ns": row["remaining_ns"],
                      "transport_rtt_ns": h4 - h1,
                      "outcome": row["outcome"]}
            controls.append(result)
            raw.append({"kind": "lease", **result})

        now = time.perf_counter_ns()
        lease_control("live-25s", now + 25_000_000_000)
        now = time.perf_counter_ns()
        lease_control("expired", now - 1_000_000)
        now = time.perf_counter_ns()
        lease_control("over-30s", now + 31_000_000_000)
        now = time.perf_counter_ns()
        lease_control("delayed-under-20s", now + 25_000_000_000, delay_s=6.0)
    finally:
        if proc.stdin:
            proc.stdin.close()
        try:
            _, stderr = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            _, stderr = proc.communicate()

    result = {
        "schema": "issue-3880-dockerdesktop-construction-v1",
        "classification": "CONSTRUCTION_ONLY_DOCKER_DESKTOP",
        "engine": "Docker Desktop linux/amd64",
        "image": args.image,
        "worker_sha256": worker_hash,
        "lease_source_sha256": lease_hash,
        "clock_samples": len(samples),
        "clock_bounds": {
            "min_lower_ns": min(row["offset_lower_ns"] for row in samples),
            "max_lower_ns": max(row["offset_lower_ns"] for row in samples),
            "min_upper_ns": min(row["offset_upper_ns"] for row in samples),
            "max_upper_ns": max(row["offset_upper_ns"] for row in samples),
            "max_bound_width_ns": max(row["bound_width_ns"] for row in samples),
            "median_roundtrip_ns": sorted(row["roundtrip_ns"] for row in samples)[len(samples)//2],
        },
        "controls": controls,
        "stderr": stderr,
    }
    (out / "raw.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in raw))
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (out / "SHA256SUMS").write_text("".join(
        f"{sha256(path)}  {path.name}\n" for path in sorted(out.iterdir()) if path.is_file()))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
