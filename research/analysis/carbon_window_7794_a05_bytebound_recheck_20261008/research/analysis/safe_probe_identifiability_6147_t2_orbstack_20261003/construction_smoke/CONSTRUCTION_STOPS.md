# T2 construction-only stops and fixes

These are construction diagnostics only, not formal candidate/auditor invocations or outcomes.

1. First host `unittest discover` attempt failed to import `Xlib` in the host Python environment (`ModuleNotFoundError`). No candidate ran. The close exception contract was moved into stdlib-only `lifecycle.py`, with the real Xlib exception type passed by `candidate.py`; this permits a meaningful host regression test while keeping the integration binding visible and container-tested.
2. After that correction, host tests passed 16/16 and the same suite passed 16/16 in the pinned OrbStack image.
3. A real construction lifecycle reproduction ran the adaptive candidate and the fixture in separate pinned containers with network disabled and read-only root filesystems. The fixture exited 0 after 44 oracle events; the candidate emitted ten rows and exited 0. Both inspect records report `OOMKilled=false`. This verifies only the teardown path, not the formal hypothesis or independent audit.

The construction raw and process inspect files are retained in `lifecycle_run_01/` with `SHA256SUMS.txt`. Formal counts remained candidate=0, auditor=0 throughout construction.
