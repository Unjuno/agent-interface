# A01 run record

**Executed:** 2026-10-05 05:21 Asia/Tokyo on Windows 11 desktop, CPython
3.11.9. Source was exported from synthetic composition tree
`22615a96e2166619933cd7fb375fc612ec30579d`, formed from main
`86a2694c6251c2d7df2f69dbea490ec037903ff7` plus PR heads #7602
`4c0123339e43bd80333118a32bc1ce625b79ff3f`, #7750
`4c7ab51a4512015a70e0e9ab90510b256b8b9cfd`, and #7769
`905816607eef1552b5e8073d95db1975de00776d`.

All three exact merge-tree operations were conflict-free. The three suites
were run once after `FREEZE.json` was committed:

- V39 typed-state/per-key projection: 35 tests, exit 0.
- Owner-issued admission identity: 3 tests, exit 0.
- Per-key cleanup bridge: 3 tests, exit 0.

Raw stdout/stderr and exact outputs are retained in the three
`*_TEST_OUTPUT.txt` files. The separate pre-freeze import-path failure is
recorded in `PREFREEZE_ATTEMPT.md` and is excluded from the A01 result.

## Interpretation

This supports only that these exact open-PR source changes can be unioned in a
synthetic tree and that their focused fake/source-level tests pass together.
It is a construction/readiness result, not a live allocation. It does not show
that a real X server emits or timestamps the events correctly, that the game
consumes input, that feedback is useful during planner latency, or that a
bounded recovery improves the outcome. The live #59 gate remains open and
unassigned.
