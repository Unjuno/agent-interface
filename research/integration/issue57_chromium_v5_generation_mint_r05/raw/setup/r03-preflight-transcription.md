# R03 import preflight transcription

Classification: preflight only, not a frozen experiment; no target method ran.

Command: with `PYTHONPATH=research/live_control`, import
`research.live_control.test_chromium_v5_generation_mint_guard_v1` to confirm
the module chain before a new run ID was frozen.

Observed result: exit code 1. The legacy imports reached
`research/observation_gating/gui_suite.py` and stopped at
`ModuleNotFoundError: No module named 'openpyxl'`.

This is a transcription of the observed shell result, not a byte-for-byte raw
stderr capture. It is excluded from all product results and is retained here
to explain why later conditions isolate only the exact V5 method.
