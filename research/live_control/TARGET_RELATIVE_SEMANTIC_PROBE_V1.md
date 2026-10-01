# Target-relative semantic probe

The Chromium completion predicate now uses a `window_content` box bound to one
coherent source surface and geometry. On each exact frame it requires the same
surface and size, translates the box by the current surface origin, and only
then hashes the RGB crop. Surface replacement, unavailable binding, resize and
out-of-frame translation return explicit false results before semantic success.
All results remain provisional, action-scoped and without input authority.

The first seed208 live allocation moved Chromium by `[21,28]`, then safely
stopped before its first pointer step. The executor still held the last observed
pre-move binding and returned `needs_decision`, with zero completed steps, no
semantic probe, no submission and empty release. Its 22 files/492,712 bytes are
retained. This establishes that external geometry change does not refresh input
authority implicitly.

V2 preserved the predicate, movement, GUI program, resize, thresholds and all
controls. It added one passive exact observation after movement and required
that observation's coherent pointer binding to equal the moved geometry. A
fresh seed211 allocation then passed all 16 formal checks:

| Measurement | Result |
|---|---:|
| Submit admission to first feedback | 148.474ms |
| Submit admission to useful feedback | 275.781ms |
| Useful probe compute | 2.743ms |
| Useful probe before PNG ready | 23.828ms |
| Useful client result before terminal | 134.919ms |

The target-relative probe succeeded with translation `[21,28]`; the fixed
screen crop failed on the same useful frame. The independent server saved
`t000211`. After completion, shrinking the same surface by 120px produced
`surface_size_changed` without hashing a crop. Exact artifact reconciliation
and empty release passed, with zero model calls and retries.

This is one scripted Linux/X11 geometry transfer, not evidence for unknown
layouts, reliability rates, model/token improvement, other operating systems or
human-tempo performance. The next interface question is how to derive and cache
the target-relative semantic region from an existing verified target handle,
then repair it after a valid resize without asking the frontier model when local
evidence is sufficient.
