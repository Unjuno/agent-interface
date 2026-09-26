# #4544 action-validity boundary construction experiment

Base: `a778bdd577b149a5ec964bbe19da533311335e2f` (main, 2026-09-27).
This is an additive, construction-only probe. It does not retry either consumed
formal allocation (990639 or 990641), alter shared guard/runtime code, launch a
game, call a model, or submit input.

## H/T/D/C/U

- **H:** If a fresh observation has a controller decision timestamp earlier
  than its capture timestamp, the running-action guard will represent a
  fail-closed disposition in its receipt: active input authority is false and
  invalidation requires a new decision. The exact amount of inversion is not
  material to ordering; the smallest discriminator is one nanosecond.
- **T:** Run the exact current-main action-validity validator and running guard
  against four deterministic cases: ACTIVE decision after capture, ACTIVE
  equality, ACTIVE decision 1ns before capture, and BETWEEN decision 1ns before
  capture. Preserve return/exception and post-call guard receipt for each.
  Run the unchanged current-main unit suites alongside this experiment in the
  pinned cached container.
- **D:** PASS only if both ordered/equal ACTIVE controls preserve authority and
  both inverted cases return a typed receipt with authority false, a recorded
  invalidation, and a new-decision requirement. A thrown exception, missing
  invalidation, or ACTIVE authority after inversion is
  `FAIL_GUARD_LOCAL_FAIL_CLOSED_BOUNDARY`. The result is scoped to this
  deterministic unit boundary; it does not classify the larger runtime.
- **C:** Use synthetic monotonic timestamps and the exact main blobs listed in
  `RESULT.md`; no clock translation, wall-clock sampling, formal seed, game,
  model, GUI, or motor input. Preserve the consumed #4544 STOP artifacts.
- **U:** The formal run's exact operands and causal clock domains remain
  unknown. Whether outer exception unwinding and verified physical release
  suffice in every integrated caller is outside this probe.

The experiment script computes its disposition from observed cases. The
independent audit consumes the retained result bytes and checks the frozen
expected outcomes without importing the candidate guard or experiment.
