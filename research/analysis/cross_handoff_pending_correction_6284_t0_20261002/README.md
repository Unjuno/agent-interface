# Issue #6284 T0 — pending-effect handoff correction

## H / T / D / C / U

**H.** Under an unchanged goal and delayed or ambiguous effect feedback, successive owners can re-issue a semantically overlapping correction under a new intent ID. The falsification target is whether this remains possible after both #24's retry/identity discipline and #5817's complete effect/resource-footprint obligation ledger are correctly applied.

**T.** Frozen, model-free finite transition table: six histories covering delayed accepted effect, ambiguous then partial effect over three owners, dedupe expiry with a new intent, unknown footprint, goal change plus mandatory safety release, and canonical resource alias. Four policies are compared: visible-state-only, typed handoff (pending reference carried but no demand conservation), correction-conservation, and #24 retry policy + #5817-style obligation ledger. Candidate and independently written audit each run once in separate pinned Docker containers. No external services, actual GUI, model, people, shared data, or production authority.

**D.** `H_FAIL_SCOPED / SUBSUMED_BY_24_5817` if the stronger D arm rejects or HOLDs every cross-handoff overlapping new-intent proposal while preserving unknown-footprint HOLD and safety-release bypass. `PASS_METHOD_SCOPED` for added correction-conservation value only if D admits a duplicate/overshooting effect on a frozen case, while the new mechanism blocks it without suppressing a changed-goal action or safety release. Any candidate/auditor disagreement is `FAIL_AUDIT`; a missing process/output/image is `STOP_INFRA`. No T1 or implementation follows from T0.

**C.** A complete resource/effect identity in #5817 may already make the cross-handoff mechanism redundant; a simple explicit owner choice may dominate both. The typed-handoff arm does not claim that an existing repository implementation is deficient; it is a stipulated comparator.

**U.** Finite synthetic transitions only. No claim that real agents generate duplicate corrections, that effect identity/footprints are complete in production, or that any mechanism improves safety, latency, or task success.

## Freeze

Allocation: `6284-PENDING-HANDOFF-CORRECTION-T0-20261002-01`. Source base: `99731a1b19e4f9d90ab58d76257b4ab23a4d8337` (main at package creation). Image: local `python:3.12-alpine`, immutable image ID/platform recorded in `FREEZE.json`; no pull. Formal invocation budget: candidate 1, independent auditor 1, retries 0. The formal input is the six-case `fixture.json`; source and fixture digests are in the freeze manifest. Construction suite ran before freeze and all tests passed.

## Result

Combined decision: `H_FAIL_SCOPED / SUBSUMED_BY_24_5817` for incremental value beyond the stronger comparator on the seven frozen synthetic histories. Formal-01's six cases show that visible-state-only and typed-handoff policies admit duplicate proposals across new intents, but #24 retry identity + #5817 obligation/footprint accounting blocks every complete-footprint overlap. Formal-02 separately verifies that D still admits a disjoint new-goal task without discharging the old unresolved operation. C (correction conservation) did not outperform D.

Both candidate/auditor pairs ran once each in pinned OrbStack Docker containers with network disabled, read-only root/source, non-root user, dropped capabilities, no-new-privileges, 0.5 CPU, 256 MiB and 64 PIDs. All four processes exited 0; there were no formal retries. Raw output and hashes are in `results/formal-01/` and `results/formal-02/`; full interpretation and limitations are in `REPORT.md`. Formal-01's omitted changed-goal positive control and one pre-container cidfile setup error are retained explicitly in its `RUN.json`, not erased.
