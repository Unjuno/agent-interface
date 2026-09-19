# MAP01 matched recovery-entry gate v2

This is a scoped, deterministic 32-vector recovery-entry classifier audit for Issue #3008. It is not a live MAP01 safety claim. `run.py` retains raw JSON; `audit.py` independently recomputes every decision and five negative controls. The workflow runs natively and in pinned `python:3.12-slim` with networking disabled.
