# Issue #2692 — live receipt transport first rung

## H / T / D / C / U

- **H:** receipts created from live GTK/X11 observations can carry identity,
  region, freshness, coverage, and effect-binding evidence to the existing O3
  evaluator without runner-synthesized positive receipts; a separately
  implemented live-source oracle will agree, and corrupted deliveries will
  fail open.
- **T:** one formal allocation, 2026-09-21, in pinned OrbStack/Docker
  `linux/arm64` image. Two separate GTK processes/windows × two regions
  (`entry`, `status`) × nine preregistered cases = 36 rows. Each row had a new
  observation UUID and monotonic intent epoch. Capture-to-arrival age limit was
  fixed at 1,000,000,000 ns. Network disabled, root filesystem read-only,
  source mounted read-only, dedicated output bind, no model client, and no
  input API. A separate Python process queried the live X server and processes
  before cleanup.
- **D:** all 36 raw X11 full-frame and region byte captures and hashes; raw
  capture events; delivery envelopes and their arrival times; gate decisions;
  GTK PID/title/XID/geometry; source generation; independent audit result;
  launch/container metadata; and cleanup status are retained in this directory.
- **C:** `PASS_LIVE_RELEVANT_REGION_FAIL_OPEN_SCOPED`: 4/4 exact current rows
  admitted, 0/32 negative rows admitted, all 32 negative rows model-escalation
  eligible, independent live X11 checks 36/36, oracle errors 0, model calls 0,
  input events 0, action emissions 0, container exit 0.
- **U:** one Xvfb server, one GTK toolkit, two static fixture processes, and
  two rectangular regions. This is transport/gate correctness only. It does
  not establish multi-application portability, visual semantics, model
  quality, token/latency benefit, task success, native desktop performance,
  or production readiness.

## Results

| Case | Rows | Admitted | Fail-open / escalation eligible |
|---|---:|---:|---:|
| complete_current | 4 | 4 | 0 |
| stale_frame | 4 | 0 | 4 |
| missing_region | 4 | 0 | 4 |
| partial_coverage | 4 | 0 | 4 |
| focus_window_change | 4 | 0 | 4 |
| generation_mismatch | 4 | 0 | 4 |
| malformed_receipt | 4 | 0 | 4 |
| authority_bearing | 4 | 0 | 4 |
| contradictory_effect_binding | 4 | 0 | 4 |

Decision: `PASS_LIVE_RELEVANT_REGION_FAIL_OPEN_SCOPED`. The full independent
oracle result is `allocations/allocation-02-live-oracle/AUDIT_RESULT.json`.
Raw bytes, receipt lineage and per-row decisions are adjacent. The separate
audit process ran before GTK/Xvfb teardown; its live-source assertions included
root-child XID, viewability, PID/title/geometry, process-start generation,
actual focus, raw full/region bytes, capture-to-arrival age, effect binding,
all case denominators and model/action accounting.

## Preserved predecessor failure

Allocation 01 is retained unmodified under `allocations/allocation-01-hold/`.
It completed 36 live captures, but its independent oracle was invoked after
source cleanup and could not connect to `DISPLAY=:99`. That allocation is
`HOLD_ORACLE_AFTER_SOURCE_CLEANUP`; allocation 02 is separately numbered and
does not overwrite or promote its result.
