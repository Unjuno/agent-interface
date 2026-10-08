# Docker-free WSL public API admission

Addresses the common pixel-assistance admission blocker in #57/#56/#2789, after
migration #6299 and capture-association fix #6307. The frozen [plan](PLAN.md),
keeper and archive precede both allocations; the keeper is preserved unchanged.
This is two fresh correctness admissions, not the planned 18-row comparison.

| Existing route | Seed | Saved A1/A2 after terminal | Input programs / emissions | Retry |
| --- | --- | --- | --- | --- |
| Ordinary persistent Python API | 1002087 | 317 / 529, PASS | 3 / 26 | 0 |
| Same API, compact presentation | 1002088 | 317 / 529, PASS | 3 / 26 | 0 |

Both use Ubuntu directly, Xvfb/Openbox, Calc 24.2, 1280x800, the same pinned
runtime archive and exact-PNG `read_cells` code inherited from compiled Calc
admission. No Docker launch, second model or installed/background sensor.
The primary chose a two-cell batch, read the original image, called the shared
read-only OCR function, then separately chose Save, explicit modal review and
confirmation. A1 and A2 read 317/529 with confidence 95.620850/95.444084 on both
routes. The blank B1 control remains UNKNOWN (confidence 0); no threshold tuning.

Original commands, replies, raw public results, image artifacts, OCR TSV/crops,
application stdout/stderr, workbook and terminal evaluation are retained under
`plain/` and `compact/`. The archive SHA is recorded in MANIFEST and allocation
records. Each has seven commands. All three input programs verify neutral release;
incremental emissions are 20 + 4 + 2 = 26 (cumulative 20/24/26 are not summed).
Owner close verifies release and closes its connection. Both owner sessions exit
0 and wait for every owned child; Calc terminates with 255 under explicit cleanup,
Openbox/Xvfb with 0. Independent XLSX evaluation occurs only after those waits.

## Actual feedback limitations and formal HOLD

Plain confirmation completes input, but the following inspection records
`TARGET_CHANGED_DURING_CAPTURE`; the public presenter withholds its image. The
primary closes the original owner without using that withheld image for reading
or new input. Preserve that failure rather than turning the nested raw artifact
into successful delivered feedback.

Compact confirmation presents an image still showing the format modal, while
post-dispatch metadata sees the main window. The primary actually viewed this
original PNG, issued no further input, closed the original owner, and subsequently
scored the saved file. Its image is not semantic completion evidence. The fixed
100ms wait is not a redraw acknowledgement; metadata and images are not atomic.

A harness defect is retained: keeper.py advances its local sequence/last_native
when a nested observation reports returned, even if public presentation withheld
that image. No read or input followed the affected plain confirmation. Before a
formal study, a successor must invalidate callback input on withheld/inconsistent
capture and prove the refusal; do not silently patch this frozen keeper.

The ordinary Python API remains an ordinary batched public baseline, not guarded
aliases or compiled.run. This manual admission does not establish its strongest
possible locally composed conditional callback baseline. Per-key guard differences
must be disclosed and fair common assistance/control semantics established before
freezing cold/warm/changed/repair/reuse schedules and gain thresholds. Python API
use does not qualify a hosted MCP endpoint, provider schema or MCP conversion.

Initial plain presentation printed encoded image text and later redundant JSON
was truncated in the outer tool output. Full original replies and native rendered
PNGs are retained. Later output replaces encoded bytes with a marker only in the
outer text presentation, then renders the exact native artifact separately. This
construction overhead belongs to the attempt; no token/compression gain is inferred.
Token/provider accounting is separately scoped if available, never missing = 0.
No matched latency, cost, peak memory, OOM-resolution or human-speed claim follows.

## Reproduction and verification

`verify.py` checks original command order, source archive identity, original PNG
hashes/embedded bytes, callback input identity/readings, incremental emissions,
neutral releases, owned-child terminal records and independent saved XLSX values.
It also checks the retained plain withheld-image outcome. Run with the existing
native Python environment, normally and under `-O`. Application profile/cache
state stays local and is excluded from publication.

The migration default remains [WSL-native](../../WSL_NATIVE.md). Docker Desktop is
stopped on the observed host; Ubuntu reports execution version 2 under WSL package
3.0.1. This study establishes direct-WSL GUI operation and shared assistance on
both public presentation routes; it does not establish causal resource savings.

## Primary accounting

The joint window includes scaffold/archive setup and both original attempts through
terminal evaluation: source lines 170836–170985,
2026-10-01T23:04:30.932Z–2026-10-01T23:14:10.882Z.
Recorded whole-context input tokens: 3,482,112; cached input
3,317,248 is a subset, uncached input
164,864; output 17,322,
reasoning 3,160 is an output subset. Total
3,499,434. Actual provider cost is unavailable/null.
This includes setup, presentation truncation and all responses in that window;
context/cache and manual pauses prevent a causal route comparison. Earlier
migration/failures and later audit/publication fall outside the window and are
not claimed free. Original 69 source records are retained with exact line identity;
the image audit finds nine native original PNG input blocks (plain four, compact
five). Encoded JSON image data is not separately counted as image input blocks.
