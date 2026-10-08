# V39 repeated same-key release identity A03

## H / T / D / C / U

**H:** For one repeated key on exact V39 opt-in V15 source closure, sequential down/up/down/up produces two distinct admissions and two distinct release receipts joined one-to-one while retaining zero inter-UP keymap queries. Overlapping duplicate down/down/up must be classified HOLD if one observed up cannot be uniquely assigned to each admission.

**T:** Run current-main V39 selector, V15 V1 release batch, V4/V3/V12 production owner chain through the current-main fake-display harness. Run exactly two sequences: sequential F8 down/up/down/up; overlapping F8 down/down/up. Persist partial raw traces after each fake input, sync, query, and emitted event.

**D:** PASS_REPEAT_JOIN only when the sequential case has two admissions, two explicit KeyRelease injections, two complete release rows, one distinct owner-thread receipt per row, unique ordered timestamp interval pairing by key/context, zero query_keymap between ups, and empty fake/backend held state. The overlap control must be HOLD_NON_BIJECTIVE when two admissions collapse to fewer distinct key-up receipts; it must never pair one release to two admissions. Any mismatch or candidate exception remains STOP/FAIL/HOLD as observed.

**C:** Fake interpreter and fake Xlib only. Server key-state/coalescing, real X event delivery, game state, and wall-clock durations are unmeasured. perf_counter_ns values are synthetic seam timing.

**U:** No X server, OS input, physical occupancy, application effect, useful feedback, live latency, threat control, bounded recovery, MAP01 outcome or human tempo is established; no live allocation is implied.

## Result

The sequential F8 down/up/down/up case emitted two admissions and two release rows, each carrying one unique owner-thread key-up receipt. Timestamp interval matching recovered two distinct episodes. The two explicit ups were separate single-row release batches in delivery order 0, 1, with zero `query_keymap` calls between them. Fake display and backend state ended empty. `physical_verification_authoritative` stayed false.

The overlapping F8 down/down/up control emitted two admissions but only one key-up injection, release row, and owner receipt. Its disposition is `HOLD_NON_BIJECTIVE`; the one up is never credited to both admissions. Fake state ended empty.

The independent raw/source audit passes. Applicable selected-path and owner/release composition tests pass 24/24 in normal Python and 24/24 under `-O`. Earlier source-closure and backend-harness STOPs and the first auditor failure are preserved.

This is a deterministic fake source-composition result only. It establishes no physical occupancy, X server/OS input, app effect, useful feedback, live latency, threat control, recovery, MAP01 outcome or human-tempo benefit. It does not satisfy the live Issue #59 gate or authorize a shared-resource allocation.

Run the read-only audit from repository root with:

`python -B research/doom/v39_samekey_repeat_a03_20261005/audit.py`
