# Bounded temporal readiness for Inkscape selection handles

Decision: **PROMOTE_BOUNDED_READINESS_WAIT_SCOPED** for selection-readiness acquisition only. This does **not** repair the stale-selection race: after readiness, every switch case still moved B rather than the revalidated A.

Scientific measured task: `INKSCAPE-SELECTION-READINESS-20260916-017`, Issue #294. Allocation 016 is retained separately as an infrastructure stop and is not pooled.

## One-factor question

The predecessor #288 / PR #293 used one screenshot after selecting A. Its full preregistered gate failed because selection handles were not visible in 4/20 first outcomes, although valid switch cases then demonstrated wrong-target effects 8/8. Here the target, SVG fixture, XTEST action, scorer, stale-selection switch and ~120 ms post-readiness effect window are unchanged. Only readiness acquisition differs:

- `snapshot`: one fresh screenshot and the same target + four-sided-selection predicate.
- `wait`: take the same first screenshot; if the identical predicate is false, repeat it at nominal 20 ms cadence for at most 300 ms. Timeout remains fail-closed and emits no effect input.

No predicate threshold, target ROI, action, scorer, or race logic differs by arm.

## Frozen design and provenance

Initial allocation 016 was preregistered in Issue #294 with 40 first cases (10 reps × stable/switch × snapshot/wait) shuffled once with `random.Random(29420260916)`. A bundled container invocation hit the outer tool limit after 15 complete cases and one empty incomplete case directory (`02-stable-wait`). Allocation 016 is stopped; none of its complete results are pooled or replayed as 017.

Allocation 017 changes orchestration only: the exact same frozen 40-case schedule is executed in bounded groups of at most four fresh processes. `prereg-017.json` SHA-256: `c9750c2b963fcba6f6dfdeb13f5dbafacb59582bc05631e7468731edf443576d`.

Measured source identities stayed unchanged:

- `run_case.py`: `cc9839b8fc70097e8d628a882bff5af55a5dbd7aafb21b3658e4caa09226757d`
- `audit.py`: `218e5892962cf5e78d429c70e694bb13b87cf90dc3482ad155b5cd382a188337`
- original frozen `prereg.json`: `96fa937107cf4b5f513a611ce3cd4a684f8a5e0f0573c1817822a0c8fe090df0`
- `environment.json`: `599018daba95831a3d42e439213f1cc798a4149d0fd3f27c320cdef2a262aa49`

Four construction cases before allocation 016 (snapshot/wait × stable/switch) all happened to be ready on their first sample. They were excluded and did not tune the 20 ms / 300 ms contract.

## First measured result — allocation 017

| endpoint | snapshot | bounded wait |
|---|---:|---:|
| cases | 20 | 20 |
| readiness accepted | **19/20** | **20/20** |
| readiness fail-closed | 1/20 | **0/20** |
| total readiness captures | 20 | 22 |
| cases requiring >1 capture | 0 | 2 |
| valid stable effects | 10/10 A-only | 10/10 A-only |
| valid switch effects | 9/9 B wrong-target | 10/10 B wrong-target |

The snapshot failure was `02-switch-snapshot`: target geometry remained scoped/current, but all four selection-handle dark-pixel counts were zero. The program stopped before `effect_start_ns` and emitted no Right-key effect.

Two wait cases (`04-stable-wait`, `08-switch-wait`) saw the same pattern on sample 0: all four handle counts were zero. Their second samples observed handles (`left=156`, `right=162`, `top=62`, `bottom=64`) and admitted the unchanged downstream action. Thus the measured benefit is explained by waiting for the *same* predicate, not by relaxing it.

The stale-intent boundary remains unchanged. Every ready switch case moved B from x=220 to230 while A remained x=50. Bounded readiness improves availability of the precondition; it does not create atomic target binding.

## Observation cost

These are descriptive local measurements, not task-speed claims.

- snapshot: 20 capture calls, cumulative capture-call wall time 657.459 ms; per-call median 31.363 ms. Readiness elapsed median 45.123 ms, max 66.377 ms.
- wait: 22 capture calls, cumulative capture-call wall time 768.710 ms; per-call median 32.006 ms. Readiness elapsed median 45.654 ms, max 133.204 ms.

The median sample count is 1 in both arms because only 2/20 wait cases needed a second sample. The mechanism adds an availability tail rather than a constant multi-frame cost in this cohort.

## ERROR CHECK

Frozen audit returns `PROMOTE_BOUNDED_READINESS_WAIT_SCOPED` with no errors: snapshot-ready19/fail1; wait-ready20/fail0; fail-closed1; snapshot stable-correct10 and switch-wrong9; wait stable-correct10 and switch-wrong10. Executed cases end with empty physical keymaps.

Five post-measurement corruption controls are rejected: schedule identity alteration, fabricated effect start on the failed-readiness case, nonempty keymap, corrupted saved SVG/effect, and missing result. These controls add no live samples.

Allocation 016's 15 complete outcomes and one incomplete directory remain separately retained; they are not statistical evidence for the 017 decision.

The compact evidence archive retains every 017 result JSON, every saved SVG, frozen sources/preregs/audit, allocation-016 stop record and complete 016 result JSONs, corruption controls, and two distinct scoped readiness crops. Full-screen 1280x800 screenshots remain local-only; result records retain their hashes. The scoped crop is the exact visual region used to distinguish handle-missing from handle-visible states.

## H / T / D / C / U

**H:** bounded waiting for the exact visible-selection predicate can recover transient selection-paint absence without weakening the predicate.

**T:** frozen 40-case live Inkscape comparison, same target/action/race/scorer; readiness acquisition only changes. Allocation 016 stopped for infrastructure and is not pooled; 017 completes the original matrix independently.

**D:** preregistered gate passes: wait 20/20 ready and snapshot has at least one readiness failure, with hard safety intact. Retain the bounded wait as a **scoped readiness mechanism**, not a stale-input fix.

**C:** readiness absence could reflect click admission or compositor paint rather than only asynchronous handle painting. The contract correctly waits for the declared observable predicate either way, but does not diagnose that internal cause.

**U:** n=20/policy, one Inkscape 1.4 fixture and Linux/X11 host, unpinned scheduling, no model, no cross-app transfer. A 300 ms bound is a chosen experiment contract, not a universal timeout. Polling can still miss or delay other predicates.

## Next single question

Do not tune cadence/deadline yet. Transfer the same `wait until declared observable predicate or timeout` contract to one **different existing real application predicate** (for example Calc's format-confirmation modal) and test whether it reduces premature actions/false absence without application-specific privileged state. Hold action policy fixed. This discriminates a reusable temporal-readiness primitive from an Inkscape-only paint workaround.
