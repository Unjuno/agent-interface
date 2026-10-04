"""MAP01 v40: v39 controller with additive per-key release telemetry."""
from __future__ import annotations

import sys
from pathlib import Path

import map01_overlap_controller_v39 as previous

HERE = Path(__file__).resolve().parent


def session_command(args, runtime):
    return [sys.executable, str(HERE / "session_map01_v14.py"),
            "--out", str(runtime), "--seed", str(args.seed),
            "--timeout-seconds", "600", "--skill", "1",
            "--load-fixture-manifest",
            str(args.load_fixture_manifest.resolve())]


def main():
    original = previous.session_command
    previous.session_command = session_command
    try:
        previous.main()
    finally:
        previous.session_command = original


if __name__ == "__main__":
    main()
