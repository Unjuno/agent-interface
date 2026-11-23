# Chromium V5 point-mint generation guard R05

**Baseline disposition: defect reproduced.** Both changed-generation controls
reached handle mint, while the unchanged-generation positive passed. The
failure reproduced in normal and optimized Python runs.

## Baseline observation

The test invoked the exact `session_v33.Backend.execute` method and the actual
`TargetHandleStore` implementation with a synthetic RGB checker image. Source
and fresh observations had identical pixels, focus, surface, and geometry.
Only one generation digest changed in each negative control. The method did
not raise `DecisionRequired` for either a changed process generation or a
changed window generation; the test's negative-case assertions failed because
mint had proceeded. The positive same-generation case passed. Normal and `-O`
each recorded two failures and one pass. Raw output and source conditions are
retained in [`raw/baseline/`](raw/baseline/).

## Repair and follow-up

`session_v33.Backend.execute` now compares both optional generation fields
between the model-source observation and the fresh mint observation after the
existing focus/surface comparison and before patch-based mint. A mismatch (or
missing-vs-present generation identity) refuses with a typed
`process_generation_changed` or `window_generation_changed` reason, records
both values and sequences, and creates no handle.

The same R05 test then passed in normal and `-O`; combined with existing target
handle semantic-binding, compiled-caller handoff, and adaptive caller/compiled
GUI tests, it passed 23/23 in each mode. That first post-fix pass used a
temporary parent-class stub at import time. R06 reran the same conditions with
a private module load that restores the stub and avoids unittest import
pollution; see the final result at [R06](../issue57_chromium_v5_generation_mint_r06/RESULT.md).

## Excluded setup attempts

- R01: stopped before method import because `lease` was not on `PYTHONPATH`.
- R02: stopped before method import because sparse checkout omitted
  `research.observation_tiles`.
- R03 preflight: the full legacy session-parent import chain required unrelated
  `openpyxl`; no method ran.
- R04: test fixture reached the real store, which correctly refused its solid
  color patch as visually flat. No generation conclusion was drawn.

Each stop is excluded and retained separately; none was silently counted as a
pass or retried under its original run ID. The `R05` scope is only a local
generation-binding contract. It does not bridge the full Chromium V5 flow into
caller v3, and it is not live GUI, provider, task-success, efficiency, recovery,
or reliability evidence. Issue #57 remains open.
