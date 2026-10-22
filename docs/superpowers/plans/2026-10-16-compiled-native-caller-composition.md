# Compiled caller / native bridge composition plan

**Goal:** Exercise the final selected target through caller v3, the exact-value
form compiler, actual guarded adapter, handle store, NativeHandleBridge and
runtime session, using Fake X transport only.

**Architecture:** Reuse the existing FakeX transport fixture. Mint real session
aliases from retained synthetic captures. Build the interface only from the
caller's final target. Delegate graph callbacks to the actual guarded adapter;
retain caller/core/native receipts and fake emissions. The synthetic task has
no independent real application score.

**Spec:** `docs/INTEGRATION_PLAN.md` stages 1–3 and
`research/live_control/COMPILED_CALLER_V3.md`.

## Constraints and review focus

No display, native input, model, provider, WSL or allocation. No producer from a
consumed historical experiment. Generation changes must stop later presses and
retain release evidence; unknown outer effect must not become task success.
No production patch unless a discriminating counterexample requires one.

- [x] Add a composed regression module using real bridge/store/session and
  guarded callbacks; cover final target promotion, unverified outer effects,
  generation changes before/during/between input, value failure/unknown and sink
  failure. Retain raw rows and bridge files.
- [x] Run normal and optimized Python; run the pinned original contradictory
  compiler as a negative control. Inspect receipts and exact fake emissions.
- [x] Run the affected selected suite and saved-only checks; preserve source
  pins, conditions, stdout/stderr and raw records without live qualification.
- [ ] Review, integrate under current main protection and exact-head checks,
  update the shared map, and remove only this task's integrated refs.
