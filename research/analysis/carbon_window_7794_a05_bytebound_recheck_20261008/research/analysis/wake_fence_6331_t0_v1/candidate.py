"""Run synthetic wake-boundary scenarios against the frozen current Lease."""
import json
import sys
from pathlib import Path

from lease import Expired, Lease


def current_lease(deadline: int, now: int) -> str:
    try:
        Lease(deadline, clock=lambda: now).check()
        return "LIVE"
    except Expired:
        return "EXPIRED"


def new_lease_after_rebind(ttl: int, now: int | None) -> str:
    if now is None:
        return "UNKNOWN_CLOCK"
    try:
        Lease(now + ttl, clock=lambda: now).check()
        return "LIVE"
    except Expired:
        return "EXPIRED"


def evaluate(s: dict, ttl: int) -> list[dict]:
    out = []
    mono = s["mono_elapsed_ns"]
    boot = s["boottime_elapsed_ns"]
    if mono is None:
        perf = "UNKNOWN_CLOCK"
    else:
        perf = current_lease(ttl, mono)
    boottime = "UNKNOWN_CLOCK" if boot is None or s["clock_coverage"] != "complete" else ("LIVE" if boot < ttl else "EXPIRED")
    if s["clock_coverage"] != "complete" or s["wake_notice"] in ("missing", "late_after_first_admission"):
        fence = {"outcome":"UNKNOWN_WAKE_COVERAGE","release_requested":bool(s["held_input"]),
                 "release_ack_observed":False,"old_generation_admitted":False,"fresh_lease_created":False,
                 "first_action":"SUPPRESS_UNKNOWN_WAKE","new_lease_outcome":"NOT_CREATED"}
    elif s["wake_notice"] == "on_time":
        if not s["release_ack"] and s["held_input"]:
            status = "SUPPRESS_PENDING_RELEASE"
        elif not s["fresh_rebind"]:
            status = "BLOCK_STALE_GENERATION"
        else:
            status = "ADMIT_FRESH_LEASE"
        fence = {"outcome":status,"release_requested":bool(s["held_input"]),
                 "release_ack_observed":bool(s["release_ack"] and s["held_input"]),
                 "old_generation_admitted":False,
                 "fresh_lease_created":bool(s["fresh_rebind"] and (s["release_ack"] or not s["held_input"])),
                 "first_action":"ADMIT_NEW_AUTHORITY" if status == "ADMIT_FRESH_LEASE" else "SUPPRESS",
                 "new_lease_outcome":new_lease_after_rebind(ttl, mono) if status == "ADMIT_FRESH_LEASE" else "NOT_CREATED"}
    else:
        fence = {"outcome":"ADMIT_CURRENT_GENERATION" if perf == "LIVE" else perf,
                 "release_requested":False,"release_ack_observed":False,
                 "old_generation_admitted":perf == "LIVE","fresh_lease_created":False,
                 "first_action":"ADMIT_OLD_AUTHORITY" if perf == "LIVE" else "SUPPRESS",
                 "new_lease_outcome":"NOT_CREATED"}
    out.extend([
        {"scenario":s["id"],"arm":"current_perf_lease","outcome":perf,
         "release_requested":False,"release_ack_observed":False,
         "old_generation_admitted":perf == "LIVE","fresh_lease_created":False,
         "first_action":"ADMIT_OLD_AUTHORITY" if perf == "LIVE" else "SUPPRESS",
         "new_lease_outcome":"NOT_CREATED"},
        {"scenario":s["id"],"arm":"boottime_deadline","outcome":boottime,
         "release_requested":False,"release_ack_observed":False,
         "old_generation_admitted":boottime == "LIVE","fresh_lease_created":False,
         "first_action":"ADMIT_OLD_AUTHORITY" if boottime == "LIVE" else "SUPPRESS",
         "new_lease_outcome":"NOT_CREATED"},
        {"scenario":s["id"],"arm":"wake_fence",**fence}
    ])
    return out


def main() -> int:
    fixture = json.loads(Path(sys.argv[1]).read_text())
    out = {"schema":"wake-fence-6331-candidate.v1","rows":[]}
    for scenario in fixture["scenarios"]:
        out["rows"].extend(evaluate(scenario, fixture["ttl_ns"]))
    Path(sys.argv[2]).write_text(json.dumps(out,sort_keys=True,separators=(",",":"))+"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
