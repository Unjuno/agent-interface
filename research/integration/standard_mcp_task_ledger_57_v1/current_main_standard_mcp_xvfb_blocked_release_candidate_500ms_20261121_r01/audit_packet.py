from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
RESEARCH = ROOT.parent
REPO = ROOT.parents[3]
PACKETS = {
    "r01": RESEARCH / "current_main_standard_mcp_xvfb_blocked_release_recheck_20261121_r01",
    "r02": RESEARCH / "current_main_standard_mcp_xvfb_blocked_release_recheck_20261121_r02",
    "r03": RESEARCH / "current_main_standard_mcp_xvfb_blocked_release_recheck_20261121_r03",
    "r04_diag": RESEARCH / "current_main_standard_mcp_xvfb_blocked_release_recheck_20261121_r04_diag",
    "r05_candidate": ROOT,
}
AUDIT_ONLY = {"SHA256SUMS", "audit.json", "audit.stdout.log", "audit.exit-code.txt", "audit_packet.py"}


def normalized_sha(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bin"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def verify_manifest(packet: Path, *, candidate: bool) -> int:
    expected: dict[str, str] = {}
    for row in (packet / "SHA256SUMS").read_text(encoding="ascii").splitlines():
        digest, relative = row.split("  ", 1)
        if relative in expected:
            raise SystemExit(f"duplicate manifest entry: {relative}")
        expected[relative] = digest
    excluded = AUDIT_ONLY if candidate else {"SHA256SUMS"}
    actual = {
        path.relative_to(packet).as_posix()
        for path in packet.rglob("*")
        if path.is_file()
        and path.relative_to(packet).as_posix() not in excluded
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    }
    if actual != set(expected):
        raise SystemExit(f"{packet.name} manifest file-set mismatch")
    for relative, digest in expected.items():
        if normalized_sha(packet / Path(*relative.split("/"))) != digest:
            raise SystemExit(f"{packet.name} checksum mismatch: {relative}")
    return len(expected)


def verify_sources(packet: Path) -> dict[str, str]:
    conditions = json.loads((packet / "conditions.json").read_text(encoding="utf-8-sig"))
    revision = conditions["source_revision"]
    blobs: dict[str, str] = {}
    for row in (packet / conditions.get("source_blobs", "source-blobs.txt")).read_text(encoding="ascii").splitlines():
        expected, relative = row.split("  ", 1)
        pinned = subprocess.check_output(["git", "rev-parse", f"{revision}:{relative}"], cwd=REPO, text=True).strip()
        if pinned != expected:
            raise SystemExit(f"{packet.name} source pin mismatch: {relative}")
        blobs[relative] = expected
    return blobs


def result(packet: Path, run: str) -> tuple[dict, int]:
    directory = packet / "runs" / run
    return (
        json.loads((directory / "result.json").read_text(encoding="utf-8")),
        int((directory / "exit-code.txt").read_text(encoding="ascii").strip()),
    )


def keys_up(row: dict) -> bool:
    return isinstance(row, dict) and bool(row) and all(value is False for value in row.values())


def main() -> None:
    manifests = {}
    sources = {}
    for name, packet in PACKETS.items():
        manifests[name] = verify_manifest(packet, candidate=name == "r05_candidate")
        sources[name] = verify_sources(packet)

    r01, r01_code = result(PACKETS["r01"], "normal")
    if r01_code != 0 or r01.get("xvfb", {}).get("status") != "unavailable" or r01.get("independent_task_oracle", {}).get("status") != "fail":
        raise SystemExit("R01 runner-deviation evidence classification changed")

    r02n, r02n_code = result(PACKETS["r02"], "normal")
    r02o, r02o_code = result(PACKETS["r02"], "optimized")
    if r02n_code != 0 or r02n.get("cancel", {}).get("owner_client_disconnect", {}).get("status") != "disconnected":
        raise SystemExit("R02 normal XRes observation changed")
    if r02n.get("independent_task_oracle", {}).get("status") != "fail":
        raise SystemExit("R02 normal task failure not preserved")
    if r02o_code != 1 or r02o.get("cancel", {}).get("owner_client_disconnect", {}).get("reason") != "supervision_timeout":
        raise SystemExit("R02 optimized timeout classification changed")

    r03 = {}
    for mode in ("optimized-01", "optimized-02", "optimized-03"):
        row, code = result(PACKETS["r03"], mode)
        disconnect = row.get("cancel", {}).get("owner_client_disconnect", {})
        if code != 1 or disconnect.get("reason") != "supervision_timeout" or not keys_up(row.get("final_cleanup", {}).get("keys_down")):
            raise SystemExit(f"R03 repeat classification changed: {mode}")
        r03[mode] = {"exit_code": code, "disconnect": disconnect.get("status"), "reason": disconnect.get("reason"), "elapsed_ms": disconnect.get("elapsed_ms"), "final_keys_up": True}

    r04, r04_code = result(PACKETS["r04_diag"], "optimized-timeout-1s")
    if r04_code != 0 or r04.get("cancel", {}).get("owner_client_disconnect", {}).get("status") != "disconnected":
        raise SystemExit("R04 diagnostic did not recover XRes observation")
    if r04.get("independent_task_oracle", {}).get("status") != "fail" or r04.get("synthetic_application_effect", {}).get("effect_count_at_horizon") == r04.get("synthetic_application_effect", {}).get("effect_count_before_cancel"):
        raise SystemExit("R04 delayed task failure was lost")

    candidate_runs = {}
    for mode in ("normal", "optimized"):
        row, code = result(ROOT, mode)
        cancel = row.get("cancel", {})
        fresh = row.get("fresh_session_recovery", {}).get("task_oracle", {})
        disconnect = cancel.get("owner_client_disconnect", {})
        old_oracle = row.get("independent_task_oracle", {})
        effect = row.get("synthetic_application_effect", {})
        release = row.get("independent_release_readback", {})
        if code != 0 or row.get("xvfb", {}).get("status") != "captured":
            raise SystemExit(f"candidate {mode} test or server provenance missing")
        if disconnect.get("status") != "disconnected" or cancel.get("owner_release_attempt", {}).get("status") != "readback_verified":
            raise SystemExit(f"candidate {mode} XRes/release receipt missing")
        if release.get("neutral") is not True or not keys_up(row.get("final_cleanup", {}).get("keys_down")):
            raise SystemExit(f"candidate {mode} neutral readback missing")
        if old_oracle.get("status") != "fail" or old_oracle.get("task_success") is not False:
            raise SystemExit(f"candidate {mode} old task failure was upgraded")
        if effect.get("effect_count_before_cancel") != [1] or effect.get("effect_count_at_horizon") == [1]:
            raise SystemExit(f"candidate {mode} old delayed effect was not retained")
        if row.get("late_request_horizon_readback", {}).get("late_keypress_a_observed") is not True:
            raise SystemExit(f"candidate {mode} late old A was not retained")
        if fresh.get("status") != "pass" or fresh.get("task_success") is not True:
            raise SystemExit(f"candidate {mode} fresh-session task outcome missing")
        if fresh.get("checks", {}).get("old_unknown_fence_preserved") is not True or fresh.get("checks", {}).get("no_old_delayed_press_after_new_session") is not True:
            raise SystemExit(f"candidate {mode} fresh-session generation isolation missing")
        if cancel.get("cleanup_status") != "UNKNOWN" or cancel.get("release_confirmed") is not False or cancel.get("replay_allowed") is not False:
            raise SystemExit(f"candidate {mode} old operation safety fence changed")
        candidate_runs[mode] = {
            "unittest_exit_code": code,
            "caller_response": row.get("cancel_response", {}).get("status"),
            "caller_cancel_ms": row.get("cancel_invocation_elapsed_ms"),
            "event_loop_max_gap_ms": row.get("cancel_event_loop_timing", {}).get("max_gap_ms"),
            "xres_disconnect_ms": disconnect.get("elapsed_ms"),
            "release_verified": True,
            "old_effect_count_before": effect.get("effect_count_before_cancel"),
            "old_effect_count_at_horizon": effect.get("effect_count_at_horizon"),
            "old_task_success": False,
            "fresh_task_success": True,
            "old_cleanup_unknown_no_replay": True,
            "final_keys_up": True,
        }

    audit = {
        "status": "PASS_AUDIT_XRES_500MS_CANDIDATE_WITH_OLD_TASK_FAILURE",
        "source_blobs_checked": {name: len(rows) for name, rows in sources.items()},
        "manifest_files_verified": manifests,
        "baseline_optimized_repeats": r03,
        "one_second_budget_diagnostic": {
            "xres_disconnect_ms": r04.get("cancel", {}).get("owner_client_disconnect", {}).get("elapsed_ms"),
            "old_effect_count_before": r04.get("synthetic_application_effect", {}).get("effect_count_before_cancel"),
            "old_effect_count_at_horizon": r04.get("synthetic_application_effect", {}).get("effect_count_at_horizon"),
            "task_oracle": r04.get("independent_task_oracle", {}).get("status"),
        },
        "candidate_runs": candidate_runs,
        "interpretation": "The 500 ms bounded XRes wait allowed disconnect/release receipts in both modes and preserved a pending public response, but the deliberately withheld cancellation acknowledgement kept the old A key held long enough for repeated A KeyPress/KeyRelease effects; the scheduled delayed B KeyPress was not observed. The old generation remained UNKNOWN and unreplayable; a separate fresh-generation task passed.",
        "not_proven": ["old task success", "late-input exclusion on original task", "reliability rate", "MAP01", "matched efficiency", "research-preview acceptance"],
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
