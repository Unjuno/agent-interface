"""Fail-closed prelaunch gate for the #5550 successor container allocation."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def assess(freeze: dict, *, current_main: str, image_digest: str, platform: str,
           running_containers: list[str], now: datetime) -> dict:
    lease = freeze.get("execution_lease")
    if not isinstance(lease, dict) or lease.get("assigned") is not True:
        reason = "STOP_NO_EXPLICIT_ASSIGNMENT"
    elif not lease.get("coordinator_comment_id") or not lease.get("owner"):
        reason = "STOP_ASSIGNMENT_PROVENANCE_INCOMPLETE"
    elif current_main != freeze.get("frozen_main"):
        reason = "STOP_MAIN_MISMATCH"
    elif image_digest != lease.get("image_digest") or platform != lease.get("platform"):
        reason = "STOP_IMAGE_OR_PLATFORM_MISMATCH"
    elif running_containers:
        reason = "STOP_RESOURCE_OCCUPIED"
    else:
        try:
            start = parse_utc(lease["start_utc"])
            end = parse_utc(lease["end_utc"])
            actual = now.astimezone(timezone.utc)
        except (KeyError, TypeError, ValueError, AttributeError):
            reason = "STOP_INVALID_WINDOW"
        else:
            if start >= end:
                reason = "STOP_INVALID_WINDOW"
            elif not start <= actual < end:
                reason = "STOP_OUTSIDE_ASSIGNED_WINDOW"
            else:
                reason = "PASS_PRELAUNCH_GATE"
    return {
        "status": reason,
        "docker_authorized_by_guard": reason == "PASS_PRELAUNCH_GATE",
        "allocation": freeze.get("allocation"),
    }


def query_running_containers(docker_context: str, *, runner=None) -> list[str]:
    if runner is None:
        runner = subprocess.run
    completed = runner(
        ["docker", "--context", docker_context, "ps", "--quiet"],
        check=True, capture_output=True, text=True, timeout=10,
    )
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def main(argv=None, *, runner=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freeze", type=Path)
    parser.add_argument("--main-sha", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--docker-context", choices=("orbstack",), required=True)
    args = parser.parse_args(argv)
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    preflight = assess(freeze, current_main=args.main_sha, image_digest=args.image_digest,
                       platform=args.platform, running_containers=[], now=now)
    if preflight["status"] != "PASS_PRELAUNCH_GATE":
        print(json.dumps(preflight, sort_keys=True, separators=(",", ":")))
        return 2
    try:
        running = query_running_containers(args.docker_context, runner=runner)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        result = {
            "status": "STOP_DOCKER_INVENTORY_UNAVAILABLE",
            "docker_authorized_by_guard": False,
            "allocation": freeze.get("allocation"),
            "error_type": type(exc).__name__,
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 2
    result = assess(freeze, current_main=args.main_sha, image_digest=args.image_digest,
                    platform=args.platform, running_containers=running, now=now)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["docker_authorized_by_guard"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
