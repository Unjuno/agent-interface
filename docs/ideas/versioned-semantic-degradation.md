# Versioned semantic degradation

This idea family asks whether an interface can preserve useful, non-consequential operations when optional services fail while keeping each operation's evidence requirements and claim ceiling explicit. A degraded mode must not extend authority, admit work without required freshness or release evidence, or describe an unverified effect as success. These are finite-method studies, not runtime fallback policy or safety authorization.

## #8609: independent optional-service failures

- **Status:** open; finite-method result recorded.
- **Idea:** Compare a versioned operation contract with all-or-nothing refusal under independent optional-service failures.
- **Outcome:** T0 A01 is `PASS_METHOD_SCOPED` for its authored finite matrix. Candidate and independent raw-only auditor each ran once with zero retries; the auditor reconstructed 1,024 rows and rejected 6/6 frozen corruptions. The versioned selector retained a supported read-only outcome in 320 rows versus 1 for the comparator (319 additional rows). All 512 pending-release rows retained release identity and blocked new action admission. The 19-file manifest matched. This does not establish live GUI behavior, runtime fallback safety, or product benefit. Evidence is in [PR #8752](https://github.com/Unjuno/agent-interface/pull/8752), which is currently open and DIRTY; its exact commit and review state must be refreshed before any integration decision.

## #8610 and #8622: common-cause dependency loss

- **Status:** both Issues remain open; preserve the original protocol mismatch and the corrected successor's custody hold.
- **Idea:** Test whether a degradation contract tracks shared dependencies rather than assuming nominally separate services fail independently.
- **#8610 A01:** The candidate and auditor each ran once, but the executed arms were binary all-route gating, dependency-aware contract, and unsafe silent substitution. The registered hypothesis required an independence-assuming lookup, dependency-aware contract, and unknown-dependency fail-closed control. Therefore the A01 method result is `HOLD_PROTOCOL_ARM_MISMATCH`; its auditor pass applies only to the executed fixture. The correction and original evidence were retained in merged [PR #8621](https://github.com/Unjuno/agent-interface/pull/8621). No retry is authorized by that record.
- **#8622 A02:** The corrected three-arm protocol ran once per candidate/auditor with zero retries. The auditor reconstructed 10 cases: the independence-assuming lookup admitted 6 unsupported operations across 4 cases; the dependency-aware policy had 0 unsupported outcomes; the unknown-dependency arm admitted 0; release obligations were labeled in 10/10 cases; dispatches were 0. The disposition remains `HOLD_RESULT_CUSTODY`: raw stdout streams were memory-only and the terminal truncated the digest strings, so digest fields were left null. Merged [PR #8625](https://github.com/Unjuno/agent-interface/pull/8625) preserves that record; it does not authorize a rerun or promote the result to a custody PASS.

## Boundary and next step

Together these records suggest a finite, testable distinction between independent component loss and shared-cause loss, but they do not establish that the authored dependency graph matches a real application. Keep unknown dependencies fail-closed. Before integration, reconcile #8752's open DIRTY evidence PR against current `main` and its retained package without changing the frozen experiment or promoting its scoped result. Any new formal run requires its own fresh, explicitly allocated successor and a new frozen source; do not reuse these allocations.
