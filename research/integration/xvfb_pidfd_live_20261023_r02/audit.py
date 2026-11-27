"""Reconstruct process-control evidence without starting or signalling anything."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent


def start_ticks(raw):
    return int(raw[raw.rfind(")") + 2:].split()[19])


def audit():
    result = json.loads((OUT / "result.json").read_text())
    conditions = json.loads((OUT / "conditions.json").read_text())
    launch = json.loads((OUT / "raw-launch.json").read_text())
    cleanup = json.loads((OUT / "cleanup-recheck.json").read_text())
    absent = json.loads(cleanup["stdout"])
    identity = json.loads((OUT / "process-started.json").read_text())
    pid = identity["pid"]
    birth = start_ticks(identity["stat"])
    checks = {
        "outer_success": launch["status"] == "COMPLETED" and launch["outer_exit_code"] == 0,
        "scoped_result": result["status"] == "PASS_PROCESS_SIGNALLING_SCOPED",
        "frozen_helper": result["source"]["normalized_sha256"] == conditions["helper_normalized_sha256"],
        "frozen_executable": result["xvfb"]["sha256"] == conditions["xvfb_sha256"],
        "all_declared_cases_once": [r["schedule"] for r in result["cases"]] == conditions["schedules"],
        "healthy_independent_stop": result["cases"][0]["stopped_readback"]["state"] in ("T", "t"),
        "cleanup_confirmed": result["cleanup"]["confirmed_exited"] is True and result["cleanup"]["exit_code"] == 0,
        "postrun_pid_and_files_absent": cleanup["outer_exit_code"] == 0 and not any(
            absent[k] for k in ("pid_exists", "lock_exists", "socket_exists")),
        "no_container_runtime": result["wslc_operations"] == 0 and result["docker_operations"] == 0,
    }
    summaries = []
    for row in result["cases"]:
        name = row["schedule"]
        signals = row["signals"]
        checks[name + ":scope"] = row["status"] == "PASS_PROCESS_SIGNALLING_SCOPED"
        checks[name + ":stop_cont"] = [r["signal"] for r in signals] == [19, 18]
        checks[name + ":owned_pidfds"] = all(
            next(line.split(":", 1)[1].strip() for line in r["fdinfo"].splitlines()
                 if line.startswith("Pid:")) == str(pid) for r in signals)
        checks[name + ":syscall_order"] = (
            signals[0]["invoked_monotonic_ns"] <= signals[0]["returned_monotonic_ns"]
            <= signals[1]["invoked_monotonic_ns"] <= signals[1]["returned_monotonic_ns"])
        observed = row["resumed_readback"]
        checks[name + ":live_same_process_after_cont"] = (
            observed["pid"] == pid and start_ticks(observed["stat"]) == birth
            and observed["state"] not in ("T", "t", "Z", "X")
            and observed["observed_monotonic_ns"] >= signals[1]["returned_monotonic_ns"])
        if name == "healthy":
            stopped = row["stopped_readback"]
            checks[name + ":same_process_observed_stopped"] = (
                stopped["pid"] == pid and start_ticks(stopped["stat"]) == birth
                and signals[0]["returned_monotonic_ns"] <= stopped["observed_monotonic_ns"]
                <= signals[1]["invoked_monotonic_ns"])
        else:
            checks[name + ":declared_fault"] = "declared injected" in row.get("exception", "")
        summaries.append({"schedule": name, "resumed_state": observed["state"],
                          "signal_request_interval_ms": (signals[1]["invoked_monotonic_ns"]
                              - signals[0]["invoked_monotonic_ns"]) / 1_000_000,
                          "inference_limit": "descriptive interval, not an effect bound"})
    if not all(checks.values()):
        raise RuntimeError({k: v for k, v in checks.items() if not v})
    return {"status": "PASS_PROCESS_SIGNALLING_SCOPED", "checks": checks,
            "descriptive_intervals": summaries,
            "limits": "One owned Xvfb, three schedules; no GUI input, release, task, efficiency or reliability proof."}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
