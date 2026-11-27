"""Independent structural audit for the before-acceptance recovery probe."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    require(len(rows) == 2, "expected exactly two mode rows")
    require({row["mode"] for row in rows} == {"normal", "optimized"},
            "normal/optimized pair is incomplete or duplicated")
    heads = {row["source_head"] for row in rows}
    backends = {row["backend_blob"] for row in rows}
    sessions = {row["session_blob"] for row in rows}
    probe_hashes = {row["probe_sha256"] for row in rows}
    require(len(heads) == len(backends) == len(sessions) == len(probe_hashes) == 1,
            "paired mode rows have mismatched source identities")
    probe = Path(__file__).with_name("probe.py")
    require(next(iter(probe_hashes)) == hashlib.sha256(
        probe.read_bytes()).hexdigest(), "probe source hash mismatch")
    root = Path(__file__).resolve().parents[3]
    head = next(iter(heads))
    subprocess.check_call(["git", "cat-file", "-e", f"{head}^{{commit}}"],
                          cwd=root, stdout=subprocess.DEVNULL)
    for path, expected in (("runtime/backends/win32_v1/backend.py",
                            next(iter(backends))),
                           ("runtime/backends/win32_v1/session.py",
                            next(iter(sessions)))):
        found = subprocess.check_output(["git", "rev-parse", f"{head}:{path}"],
                                        cwd=root, text=True).strip()
        require(found == expected, f"source blob mismatch for {path}")

    modes = []
    for row in rows:
        recovery = row["after_recovery"]
        before = row["before_recovery"]
        late = row["after_late_down_before_old_call_return"]
        final = row["after_old_call_return"]
        rr = recovery["result"]
        require(before["events"] == [] and before["api_keys_down"] == []
                and before["backend_held_keys"] == {}
                and before["session_recovery_required"] is False,
                f"{row['mode']}: API or ledger changed before DOWN acceptance")
        require(rr.get("status") == "refused"
                and rr.get("error") == "INPUT_RECOVERY_NOT_REQUIRED"
                and rr.get("release_attempted") is False
                and recovery["events"] == []
                and recovery["api_keys_down"] == [],
                f"{row['mode']}: unexpected public recovery result")
        require(recovery["returned_ns"] >= recovery["started_ns"]
                and recovery["response_ms"] >= 0,
                f"{row['mode']}: invalid recovery timing")
        late_events = late["events"]
        require([event["kind"] for event in late_events] == ["old_down"]
                and late["api_keys_down"] == [17],
                f"{row['mode']}: no late DOWN before old API return")
        final_events = final["events"]
        require([event["kind"] for event in final_events] == ["old_down", "up"]
                and final["api_keys_down"] == []
                and final["dispatch_result"].get("status") == "completed",
                f"{row['mode']}: terminal cleanup differs")
        require(final_events[0]["accepted_ns"] > recovery["returned_ns"]
                and final_events[1]["accepted_ns"] > final_events[0]["accepted_ns"],
                f"{row['mode']}: expected recovery < late DOWN < terminal UP")
        modes.append({"mode": row["mode"],
                      "recovery_error": rr["error"],
                      "recovery_emitted_no_input": True,
                      "late_down_after_recovery_return": True,
                      "terminal_cleanup_restored_fake_neutrality": True,
                      "recovery_response_ms": recovery["response_ms"]})

    result = {
        "schema": "win32-before-accept-blocked-recovery-audit-r01",
        "status": "PASS_SYNTHETIC_SCHEDULE",
        "auditor_python": platform.python_version(),
        "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "source_head": head,
        "backend_blob": next(iter(backends)),
        "session_blob": next(iter(sessions)),
        "probe_sha256": next(iter(probe_hashes)),
        "modes": modes,
        "scope": "structural audit of inert user32 schedule only",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, ensure_ascii=False)
                           + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "modes": modes}, sort_keys=True))


if __name__ == "__main__":
    main()
