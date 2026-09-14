"""Freeze a fresh matched integration pair for combined observe-target."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/chromium-observe-target-pair-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    names = [
        "preregister_chromium_observe_target_pair_v1.py",
        "run_chromium_observe_target_pair_v1.py",
        "target_handle_chromium_socket_v4.py",
        "interactive_target_handle_chromium_v4.py",
        "session_v32.py", "observe_target_handle_v1.py",
        "session_v31.py", "session_v30.py", "session_v29.py",
        "scoped_target_handle_v3.py", "scoped_target_handle_v2.py",
        "durable_submit_v4.py", "append_checkpoint_v1.py",
        "received_continuation_v1.py", "received_exchange_v2.py",
    ]
    plan = {
        "status": "preregistered_before_fresh_live_execution",
        "study": "chromium-observe-target-pair-01",
        "execution_order": [
            {"mode": "combined", "seed": 991012},
            {"mode": "separate", "seed": 991012},
        ],
        "fixed_difference": (
            "combined uses one observe_target_handle submit; separate uses one "
            "observe submit followed by one target_handle_query submit"
        ),
        "promotion": (
            "both independent saves pass, both checks and admission revalidations "
            "pass, combined check binds the returned observation identity exactly, "
            "all input releases, and combined uses exactly two fewer durable calls"
        ),
        "failure_policy": "retain first allocation; no rerun or coordinate/box repair",
        "known_probe_failures": [
            "initial Windows import stopped before probe because Xlib was unavailable",
            "first extracted probe revision retained obsolete Backend name",
            "second extracted probe revision omitted fixture observation method",
        ],
        "sources": {name: sha(HERE / name) for name in names},
        "scope": (
            "two fresh scripted Chromium X11 sessions on one new seed; matched "
            "operation-level integration; no model call, causal latency, token, "
            "human-speed, cross-domain or default-promotion claim"
        ),
    }
    (OUT / "preregistration.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
