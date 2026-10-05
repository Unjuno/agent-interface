"""Read-only source audit for the frozen main measurement-clock contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASE = "e7c916989da30741b00c234efd264067d0899851"
SOURCES = (
    "research/live_control/input_transition_owner_v3.py",
    "research/live_control/input_transition_owner_v4.py",
    "research/live_control/input_owner_v12.py",
    "research/doom/doom_owner_thread_release_batch_backend_v1.py",
    "research/doom/main_thread_scorer_polling_v1.py",
    "research/doom/map01_scorer_stdio_adapter_v1.py",
    "research/doom/independent_progress_clock_v2.py",
    "research/doom/session_map01_v15.py",
)


def main() -> None:
    def show(name: str) -> bytes:
        return subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{BASE}:{name}"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout

    raw = {name: show(name) for name in SOURCES}
    source = {name: data.decode("utf-8") for name, data in raw.items()}
    checks = {
        "release_caller_uses_perf_counter_ns":
            "release_call_started_ns = time.perf_counter_ns()" in source[SOURCES[0]]
            and "release_call_returned_ns = time.perf_counter_ns()" in source[SOURCES[0]],
        "owner_brackets_keyrelease_and_sync":
            "owner_keyrelease_started_ns = time.perf_counter_ns()" in source[SOURCES[2]]
            and "owner_sync_returned_ns = time.perf_counter_ns()" in source[SOURCES[2]]
            and "xtest.fake_input(d, X.KeyRelease, code)" in source[SOURCES[2]]
            and "d.sync()" in source[SOURCES[2]],
        "receipt_explicitly_limits_sync_claim":
            "XSync does not prove application use" in source[SOURCES[1]],
        "release_batch_samples_after_last_up":
            "latest_return <= sample_started <= sample_finished" in source[SOURCES[3]]
            and "after = self.owner.call(\"input_state\")" in source[SOURCES[3]],
        "release_rows_published_after_batch_sample":
            source[SOURCES[3]].index("after = self.owner.call(\"input_state\")")
            < source[SOURCES[3]].index("self.emit(row)", source[SOURCES[3]].index(
                "def _publish_release_batch")),
        "scorer_clock_is_perf_counter_ns":
            "clock_ns: ClockNs = time.perf_counter_ns" in source[SOURCES[4]],
        "scorer_state_read_window_is_recorded":
            '"sample_started_ns": sample_started_ns' in source[SOURCES[4]]
            and '"sample_finished_ns": sample_finished_ns' in source[SOURCES[4]],
        "v15_sampling_path_uses_35_hz_and_same_clock":
            "time.perf_counter_ns,attempts=3" in source[SOURCES[7]]
            and "sample_hz=35.0" in source[SOURCES[7]],
        "progress_events_are_independent_and_typed":
            "row['controller_visible']=False" in source[SOURCES[5]]
            and "useful=True" in source[SOURCES[6]],
    }
    if not all(checks.values()):
        raise SystemExit(json.dumps({"status": "FAIL", "checks": checks}, indent=2))
    hashes = {
        name: hashlib.sha256(raw[name]).hexdigest() for name in SOURCES
    }
    print(json.dumps({
        "status": "PASS_SCOPED_SOURCE_CLOCK_COMPATIBILITY",
        "base_commit": BASE,
        "checks": checks,
        "source_sha256": hashes,
        "scope": "source semantics only; no live runtime, X server, game, model, physical state, or task-effect run",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
