# Belief-space recovery and observation-predicate refinement

This family asks what a finite partial-observation model can establish about safe recovery, and how its abstraction should be checked and refined. The records are synthetic method evidence or proposals only. They do not authorize live probing, GUI actions, or a runtime recovery policy.

## #8527: bounded belief-space recovery

- **Status:** open; no formal result recorded.
- **Idea:** Distinguish statewise recoverability from whether one observation-contingent policy safely recovers an entire belief set before a finite control window expires.
- **Outcome:** The first construction STOP was outside an isolated container and did not produce a frozen allocation or formal candidate/auditor run. The additive A02 package in draft [PR #8554](https://github.com/Unjuno/agent-interface/pull/8554) records 10/10 construction tests in both normal and optimized Python, but formal candidate, auditor and container invocations remain zero under `HOLD_WSLC_CLIENT_OWNERSHIP_UNKNOWN`. Do not treat construction checks as an experiment result.

## #8553: abstraction-refinement method and audit qualification

- **Status:** open; preserve A01's historical label with the later audit gap, and keep A02's pre-run hold separate from A03.
- **Idea:** Test whether finite recovery classifications change when the abstraction is refined only where a counterexample shows the abstraction matters.
- **A01:** Merged [PR #8559](https://github.com/Unjuno/agent-interface/pull/8559) recorded a `PASS_METHOD_SCOPED` finite result. A later independent read-only audit found that the auditor did not bind policy branch values to their declared safe observation feature/domain, and the retained manifest did not match three stdout files. These findings do not prove the saved policy is wrong, but the original PASS does not establish the branch-safety gate or authenticate those three outputs.
- **A02:** `HOLD_MAIN_ADVANCED_PRE_RUN`; the frozen main SHA changed before execution. Candidate/diagnostic/auditor counts stayed 0/0/0. No retry or result substitution.
- **A03:** The audit-only replay confirmed the branch-binding gap: the legacy checker accepted both unsupported observation signatures and swapped child policies; the independent replay rejected both mutations and reconstructed the retained 2 policy trees / 5 cases. Candidate generation stayed at zero; diagnostic and auditor ran once each. Merged A01 output and label remain unchanged. The additive report is in open [PR #8824](https://github.com/Unjuno/agent-interface/pull/8824), currently CLEAN with review pending.

## #8562: bounded synthesis of new safe predicates

- **Status:** open; unverified proposal, T0 not run.
- **Idea:** Test whether an explicitly allowlisted observation-expression grammar can synthesize a safe separator when the existing predicate catalog cannot. This is a bounded transfer proposal, not a new general CEGAR/CEGIS method.
- **Readiness:** The latest issue update retains an ownership and cleanup-verification HOLD under [#7924](https://github.com/Unjuno/agent-interface/issues/7924). It forbids starting the proposed WSLc T0 until an authorized owner records lane reconciliation/release and exact cleanup state. No image/container operation or T0 run is reported here.

## Boundary and next step

Keep #8527's belief-policy question, #8553's abstraction-adequacy and audit-binding questions, and #8562's predicate-synthesis question distinct. The existing results are finite and host-only; the initial #8527 proposal has no formal result, #8553's PASS requires the stated audit qualification, and #8562 remains on hold. Any further execution must use a fresh authorized allocation after its own source, ownership, and environment gates are satisfied.
