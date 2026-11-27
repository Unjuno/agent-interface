"""Independent structural audit of the R01 mode-specific result rows."""
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
    raw_bytes = args.input.read_bytes()
    rows = [json.loads(line) for line in raw_bytes.splitlines() if line.strip()]
    require(len(rows) == 2, "expected exactly two retained mode rows")
    require({row["mode"] for row in rows} == {"normal", "optimized"},
            "normal/optimized pair is incomplete or duplicated")
    source_heads = {row["source_head"] for row in rows}
    backend_blobs = {row["backend_blob"] for row in rows}
    session_blobs = {row["session_blob"] for row in rows}
    probe_hashes = {row["probe_sha256"] for row in rows}
    require(len(source_heads) == len(backend_blobs) == len(session_blobs) == 1,
            "paired modes do not share source identity")
    require(len(probe_hashes) == 1, "probe source hash differs across rows")
    repo_root = Path(__file__).resolve().parents[3]
    probe_path = Path(__file__).with_name("probe.py")
    require(next(iter(probe_hashes)) == hashlib.sha256(
        probe_path.read_bytes()).hexdigest(), "probe source hash mismatch")
    source_head = next(iter(source_heads))
    subprocess.check_call(["git", "cat-file", "-e", f"{source_head}^{{commit}}"],
                          cwd=repo_root, stdout=subprocess.DEVNULL)
    for path, expected in (("runtime/backends/win32_v1/backend.py",
                            next(iter(backend_blobs))),
                           ("runtime/backends/win32_v1/session.py",
                            next(iter(session_blobs)))):
        actual = subprocess.check_output(
            ["git", "rev-parse", f"{source_head}:{path}"],
            cwd=repo_root, text=True).strip()
        require(actual == expected, f"source blob mismatch for {path}")

    timelines = []
    for row in rows:
        pre = row["pre_acceptance"]
        early = row["early_up"]
        late = row["late_down_before_old_call_return"]
        final = row["after_old_call_return"]
        require(pre["fake_keys_down"] == [] and pre["events"] == [],
                f"{row['mode']}: input changed before acceptance")
        require(early["sender"].startswith("counterfactual direct"),
                f"{row['mode']}: early UP not labeled as counterfactual")
        require([event["kind"] for event in early["events"]] == ["up"]
                and early["fake_keys_down"] == [],
                f"{row['mode']}: early UP condition failed")
        require([event["kind"] for event in late["events"]]
                == ["up", "old_down"] and late["fake_keys_down"] == [17],
                f"{row['mode']}: late-DOWN counterexample absent")
        require([event["kind"] for event in final["events"]]
                == ["up", "old_down", "up"] and final["fake_keys_down"] == [],
                f"{row['mode']}: ordinary terminal cleanup result differs")
        event_times = [event["accepted_ns"] for event in final["events"]]
        require(event_times == sorted(event_times)
                and len(set(event_times)) == len(event_times),
                f"{row['mode']}: event timestamps are not strictly ordered")
        timelines.append({"mode": row["mode"], "event_order": [
            event["kind"] for event in final["events"]],
            "down_after_late_down": late["fake_keys_down"],
            "down_after_terminal_cleanup": final["fake_keys_down"],
            "event_timestamps_strictly_increasing": True})

    result = {
        "schema": "win32-late-down-after-early-up-audit-r01",
        "status": "PASS_SYNTHETIC_COUNTEREXAMPLE",
        "auditor_python": platform.python_version(),
        "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "source_head": next(iter(source_heads)),
        "backend_blob": next(iter(backend_blobs)),
        "session_blob": next(iter(session_blobs)),
        "probe_sha256": next(iter(probe_hashes)),
        "modes": timelines,
        "scope": "structural audit of an inert fake schedule; no Windows behavior inferred",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, ensure_ascii=False)
                           + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "modes": timelines},
                     sort_keys=True))


if __name__ == "__main__":
    main()
