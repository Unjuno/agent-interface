# Issue #5265 — cross-producer semantic effect coalescing

## Intake and separation

- Main at intake: `70b69b47845b35afde59c2a5f0b56c6f906c6904`.
- Issue #5265 is open. No #5265 branch or PR was found at intake.
- This is an authority-neutral finite state-machine rung. It does not change runtime code or reuse #24's same-producer retry semantics.
- The experiment uses host CPython only. Docker Desktop is present, but the shared-container queue requires a new exact assignment after prior off-lane use; this experiment does not request or use a container, GPU, model, GUI, network, or task input.

## H / T / D / C / U

**H.** Given a frozen effect-opportunity identity, a semantic coalescer will reduce equivalent same-state proposals from two producers to one simulated effect, while preserving distinct effects after target-incarnation, intent, state-generation, effect-opportunity, parameter, or deadline changes. Missing identity yields; already-satisfied work becomes `NO_ACTION`; same-producer retries remain delegated to #24.

**T.** Compare `NO_CROSS_PRODUCER_COALESCING` with `SEMANTIC_EFFECT_COALESCING` over the ten hand-authored cases in `workload.json`. Candidate identity is intent revision, state generation, target identity/incarnation, operation, effect class/opportunity, expected postcondition, parameters, and deadline. Proposal and producer IDs are retained as group provenance, not used to prevent equivalent cross-producer proposals from joining. Each policy receives the same immutable proposal values. A separately implemented oracle reconstructs expected decisions and group membership from the frozen input. The ten directed cases include the eight required Issue cases plus distinct-deadline and expired-proposal boundaries.

**D.** `PASS_CROSS_PRODUCER_EFFECT_COALESCING_SCOPED` only if (1) equivalent cross-producer proposals produce 2 effects under the control and 1 under the candidate; (2) target-incarnation, intent, state-generation/effect-opportunity, parameter, and deadline changes never false-coalesce; (3) late satisfied proposals are `NO_ACTION`; same-producer retries defer to #24; missing/expired identity yields without an effect; (4) every proposal and producer ID remains attributable; (5) the independent raw audit reconstructs all rows with zero disagreement and rejects all 7 corruption controls; and (6) no authority/currentness/effect-truth claim appears. Any mismatch is retained as FAIL/STOP, not tuned or rerun.

**C.** The fixed workload and deterministic simulator omit scheduling races, concurrent admission, effect observation delay, event loss, application behavior, and #732 single-writer/resource-conflict handling. They can make coalescing look cleaner than a real concurrent runtime.

**U.** This can establish only behavior of this synthetic state machine. It cannot establish arbitrary-GUI exactly-once behavior, safe live effects, production integration, or that a new abstraction is needed after #24/#732 are composed. No runtime change or live rung is authorized by this result.

## Frozen execution boundary

The allocation, exact source/workload hashes, commands, interpreter, and unique output paths are in `FREEZE.json`. Run construction tests before freezing. Publish/read back the freeze before the sole formal host invocation. Run one separate CPU-only auditor only after a successful formal exit and raw hash capture. Any source/base/output drift before invocation means STOP; never retry or select a replacement case set.
