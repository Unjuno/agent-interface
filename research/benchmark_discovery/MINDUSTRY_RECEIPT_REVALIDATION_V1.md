# Mindustry receipt target revalidation v1

Issue #55 asks whether a target derived from a receipt still belongs to current
pixels after planner wait. A valid receipt and elapsed-time freshness alone are
insufficient: the runtime must acquire a new post-decision observation, bind it
to the same focus/surface/geometry, and locally revalidate the checked pixels
before target input.

## Candidate boundary

`receipt_target_admission_v1.py` is a model-free authority check. It accepts a
source receipt, decision sequence, current observation and one to eight pixel
dependencies. Dependencies are either an exact patch or a stable change mask
from baseline to receipt/current pixels. It returns `TARGET_REFERENCE_ONLY`
with a point only when every dependency remains valid. Missing history, a clock
only, stale evidence, focus/surface changes, resize, out-of-surface points and
pixel changes return `NO_TARGET_AUTHORITY` with a null point and typed reason.

`mindustry_receipt_session_v1.py` retains bounded exact observations and adds
`pointer_click_receipt_target`. It takes a fresh snapshot after the model
decision, emits the revalidation result, and reaches the existing pointer
admission/release path only after a positive local result. The trace therefore
keeps source receipt -> model decision -> current revalidation -> input
admission in order.

The no-GUI probe covers a positive exact dependency, a positive translated
surface, changed exact pixels, changed stable mask, missing history, clock-only
same-sequence evidence, staleness, focus change and resize. Its adapter is never
called on a refusal. The probe passes on Windows and WSL.

## Frozen live block

The driver and condition order were frozen before GUI allocation. All four
conditions use the same Linux/X11 fixture, Luna-low planner, task prompts and
independent engine scorer. There were no condition retries and no subagents.
The first accidental Windows launcher invocation failed on Linux-only `fcntl`
before GUI, socket or model startup and is preserved separately. The intended
WSL/X11 allocation then ran once.

| Condition | Revalidation and admitted target input | Independent task | Calls / input tokens | Exchanges / exact frames | Decision to evaluation |
|---|---|---:|---:|---:|---:|
| unchanged positive | palette and world both `all_dependencies_revalidated`; `select-conveyor`, then `place-one-conveyor` | pass | 4 / 45,640 | 14 / 33 | 57.861 s |
| changed palette | palette `exact_dependency_changed`; no target button | fail, state preserved | 2 / 17,391 | 8 / 9 | 19.892 s |
| changed world | palette passes; world `stable_change_mask_changed`; selection only, no placement | fail, state preserved | 4 / 35,021 | 12 / 25 | 45.042 s |
| focus unavailable control | `focus_or_surface_changed`; no target button; focus restored | fail, state preserved | 2 / 17,391 | 10 / 8 | 20.510 s |

The positive palette check-to-button acknowledgement is 35.207 ms and the
world interval is 34.639 ms. Changed-world palette check-to-button is 36.151 ms.
These are local measured intervals, not an atomic OS guarantee. Positive
checked submit-to-return is 2,232.615 ms for the palette and 1,305.042 ms for
the world. The four conditions total 12 attempted and completed model calls,
115,443 input tokens (14,848 reported cached subset), 1,971 output tokens,
1,191 reasoning tokens, 44 socket exchanges and 75 exact frames.

## Formal result and interpretation

The top-level formal result is **false**. The focus condition preregistered
`current_evidence_unavailable`, while the fresh observation was available from
a different focused X11 surface and the checker returned the more specific
`focus_or_surface_changed`. Operational authority was still
`NO_TARGET_AUTHORITY`, the point was null, no target button was admitted, and
focus was restored. The mismatch is retained without retry or relabelling.

The independent audit reconstructs every raw model output, attempt/usage
ledger, socket event slice, frame, revalidation result, event order, button and
release, focus restoration, engine score, cleanup, and source/cache hash. It
passes on Windows and WSL while explicitly recording `formal_block_passed:
false` and `RETAIN_RECEIPT_REVALIDATION_WITH_DIAGNOSTIC_MISMATCH`.

Compared descriptively with the earlier v5 positive (34,967 input tokens,
53.463 s, 14 exchanges, 33 frames), this positive uses 45,640 input tokens and
57.861 s with the same exchange/frame counts. Service, cache and runtime differ,
so this is not a causal slowdown or improvement claim. Exact patches can refuse
animation/restyling; a stable binary change mask can preserve shape while its
meaning changes. The OS input race is not removed. A truly unavailable current
binding and a live resize branch remain unexecuted, so Issue #55 stays open.

The later [v3 follow-up](MINDUSTRY_RECEIPT_REVALIDATION_FOLLOWUP_V3.md)
executes both remaining branches through the same checked-click operation.
A real X11 observation with `pointer_binding: null` returns
`current_evidence_unavailable`; a real Mindustry surface resize returns
`surface_size_changed`. Both expose no authority or point, admit zero target
buttons and restore the original binding/geometry. The passing follow-up uses
four model calls, 34,806 input tokens, 20 exchanges and 15 exact frames. Its two
earlier setup failures remain preserved. With that follow-up, Issue #55's finite
engineering acceptance is covered; the non-atomic OS interval and semantic
limits remain architecture risks rather than missing branches.

## Evidence

- Frozen preregistration and report: `results/mindustry-receipt-revalidation-01/`
- Independent audit: `results/mindustry-receipt-revalidation-01/audit.json`
- No-GUI probe outputs: `probe-windows.txt`, `probe-wsl.txt`
- Audit outputs: `audit-windows.txt`, `audit-wsl.txt`
- Preserved pre-GUI launcher failure: `driver-attempt-windows-stdout.txt`,
  `driver-attempt-windows-stderr.txt`
