# V39 renewal invalidation A01

Issue #59 successor evidence for a distinct rejected-renewal admission ordering. Read [FREEZE.md](FREEZE.md) and [RESULT.md](RESULT.md). Reproduction harness uses only Python's standard library and extracts the production main-branch and helper functions; it does not import or run the game/runtime.

```powershell
python candidate_test.py research/doom/map01_overlap_controller_v39.py
python audit.py research/doom/map01_overlap_controller_v39.py
```

Pinned parent: PR #7904 head `1403c822609395f9ab21e0cdbb36b7b4c8ee044d`. WSLc execution is STOP, not PASS, pending resource recovery.
