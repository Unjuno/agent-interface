# Temporal stream restart/resume — exact-prefix replay versus result-only state

Issue: #4447. Allocation: `temporal-stream-resume-20260926-01`.

## H
A PENDING temporal obligation is not fully represented by its last emitted status plus cursor/tick. Exact replay of a retained source prefix into fresh byte-identical monitors, bound to epoch/ordinal/last-tick/prefix-digest/historical-result, should reproduce uninterrupted suffix decisions across every retained restart cut. A result-only resume comparator should expose at least one mismatch.

## T
No new X11/model/task-input work. Use exactly 24 immutable retained notification streams from #4220/#4433. Every cut after >=1 event and before stream end yields 48 restart cases. Each case starts a prepare subprocess, waits for its exit, then starts a fresh replay-resume subprocess and a separate result-only comparator subprocess. Six corruption cases mutate epoch, ordinal, last tick, prefix digest, retained result, or prefix bytes. Total 54 cases in six immutable 9-case batches; case timeout 8 s. Batch order is case IDs 0..53; each batch is invoked once and a complete preceding batch is required before the next.

The candidate reconstructs state only by replaying exact retained prefix bytes. It does not deserialize implementation-private monitor objects. The comparator restores cursor/tick and emitted statuses only; PENDING anchors/labels are absent. Both are authority-neutral.

## D
`PASS_TEMPORAL_STREAM_REPLAY_RESUME_SCOPED` iff all54 first cases plus six actual batch exits are retained; replay candidate equals an independent uninterrupted oracle in 48/48 cutpoints; comparator disagrees in >0 frozen cutpoints; all six typed corruption cases refuse; process/checkpoint/source identities reconcile; authority none/task_success null/input_dispatched false; independent raw audit errors=[]; ten effective copied-evidence mutations reject. Complete no-discriminator => HOLD_RESULT_ONLY_NOT_EXPOSED. Candidate mismatch => FAIL_TEMPORAL_RESUME_RECONSTRUCTION. Missing raw/source/process/batch evidence => HOLD/STOP.

## C
Replay stores more state and performs more work, so this is a sufficiency boundary, not an equal-cost performance comparison. Result-only is an authored diagnostic, not alleged production behavior. Reusing retained source streams means the 48 cutpoints are deterministic coverage cells, not independent natural trials.

## U
No crash/power-loss durability, storage corruption, reconnect completeness, concurrent writers, prefix GC/compaction, authentication, optimized stable monitor-state serialization, live application effect, model usefulness, tokens/latency or production promotion.

## Variables / types
| field | meaning | unit | type / bound |
|---|---|---|---|
| epoch | source-channel identity | 1 | non-empty UTF-8 string |
| ordinal | contiguous event position | 1 | exact integer >=1, Boolean forbidden |
| server_ms | retained X-server tick | ms (encoded) | exact integer [0,2^32) |
| delta_ms | A→B source-time allowance | ms | exact integer 80 |
| prefix_sha256 | exact canonical retained prefix commitment | 1 | 64-char hex string |
| last_tick | last retained source tick in prefix | ms (encoded) | exact integer |
| historical_result | last emitted three-policy result | 1 | enum record |
| cut | retained prefix length | 1 | integer 1..len(events)-1 |

Dimension rule: only X-server millisecond ticks are used for temporal-contract arithmetic. Host `monotonic_ns` timestamps bracket processes only and are never subtracted from source ticks.

## Construction chronology
- construction-01: prototype unittest was launched outside the study directory and failed import (`ModuleNotFoundError: resume`) before a scientific/restart row. Formal0.
- construction-02: corrected cwd; 4/4 pure units pass.
- construction-03: process-bound implementation; 5/5 units pass, including actual prepare-process exit followed by fresh replay/comparator processes on a disjoint synthetic A/B/H stream. A separate environment/hash command once omitted `cd` and failed before source hashing; corrected command changes no source semantics. Formal0.

## Formal execution / no-retry rule
After exact GitHub source/gate readback, invoke batches 0..5 exactly once. If any batch fails/incompletes, stop the allocation and retain it; do not continue or replace rows. Postformal audit/control code is frozen here. No gate tuning after outcomes.
