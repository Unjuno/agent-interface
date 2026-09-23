"""Run the unchanged one-click-corrected pair in preregistered reverse order."""
from pathlib import Path

import run_openttd_target_guard_live_v2 as candidate


candidate.OUT = Path(__file__).resolve().parent / "results/openttd-target-guard-live-03"


if __name__ == "__main__":
    candidate.main()
