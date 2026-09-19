"""Apply the window-binding origin delta to the frozen transformed-view runner."""
from pathlib import Path

import run_openttd_target_guard_transform_v1 as implementation


implementation.OUT = Path(__file__).resolve().parent / "results/openttd-target-guard-transform-02"
implementation.DX = -128
implementation.DY = 0
implementation.FIRST = implementation.translate(implementation.BASE_FIRST)
implementation.CONTINUATION = implementation.translate(implementation.BASE_CONTINUATION)
implementation.main()
