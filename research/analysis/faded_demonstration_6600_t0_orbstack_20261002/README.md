# Issue #6600 — faded demonstration T0

T0 is a model-free finite method check for an optional, effect-verified teaching step. It does not test human learning, participant comprehension, usability or task benefit. No teaching feature or action authority is implemented.

## H / T / D / C / U

- **H:** A source/effect-bound trace gate can distinguish verified safe reversible practice from uncertain/false/wrong-target/stale/unsafe traces, while preserving skip/stop and never minting action authority. Failure of any control rejects the method for this fixture.
- **T:** Nine deterministic rows: verified reversible effect, uncertain effect, wrong target, stale source generation, missing release, irreversible effect, ambiguous target, opt-out, and a false success claim. Compare planned success versus independently verified target/effect; include task target, release, source generation, reversibility, ambiguity and opt-in. Candidate gets public fixture only; independent auditor gets hidden oracle and raw. One candidate and one auditor, separate offline digest-pinned OrbStack containers. No participants, GUI, model, or input.
- **D:** `PASS_METHOD_SCOPED` only if all rows reconstruct, only one safe reversible verified case offers a practice step, false/uncertain/stale/wrong-target evidence is not presented as demonstrated, irreversible/ambiguous/opt-out rows are not offered, missing release blocks safe completion, stale coordinates are never reused, and skip/stop/action-authority invariants hold. Otherwise `FAIL_METHOD`; launch failure is STOP, no retry.
- **C:** All evidence, cases, response semantics and correct targets are authored; real GUI effect receipts may be incomplete or untrustworthy, and task practice may not teach.
- **U:** No human learning/retention, accessibility, time/effort, preference, real app, safety, or generalized GUI claim. T1 needs separate informed consent, privacy and disposable-app approval.

## Reproduction and disposition

Frozen commands/identities/results are in `RUN_PROTOCOL.md`, `FREEZE.json`, and allocation reports under `formal_01_20261002/`. Mutation tests are construction checks, not human outcome evidence.
