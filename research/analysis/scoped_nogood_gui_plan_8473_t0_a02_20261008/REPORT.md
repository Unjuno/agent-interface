# Issue #8473 T0 A02 — result

## Disposition

PASS_METHOD_SCOPED for the authored finite symbolic fixture. The source-scoped temporary no-good reduced repeated equivalent infeasibility checks from one to zero in each of the two recovery cases while preserving the feasible alternative. A global action blacklist suppressed those alternatives after recovery. The scoped policy also rechecked and succeeded after evidence-generation change, after same-generation expiry, after UNKNOWN, and after TIMEOUT; the complete no-alternative case ended with no effect.

The independent auditor reconstructed all 21 scenario-policy runs with no errors and rejected all five frozen corruptions. Candidate and auditor each ran once in separate pinned OrbStack containers, both exit 0; retries 0.

## Key observations

| Scenario | NO_FEEDBACK | GLOBAL_BLACKLIST | SCOPED_NOGOOD |
|---|---:|---:|---:|
| Occlusion with rearrangement | 4 checks, effect | 1 check, no plan | 3 checks, effect |
| Focus recovery | 4 checks, effect | 1 check, no plan | 3 checks, effect |
| No alternative | 2 checks, no plan | 1 check, no plan | 1 check, no plan |
| Generation changes | 2 checks, effect | 1 check, no plan | 2 checks, effect |
| No-good expires | 2 checks, effect | 1 check, no plan | 2 checks, effect |
| Unmodeled UNKNOWN | 2 checks, effect after recheck | 2 checks, effect | 2 checks, effect |
| TIMEOUT | 2 checks, effect after recheck | 2 checks, effect | 2 checks, effect |

The infeasibility query reduction is one duplicate query per recovery scenario in this fixed proposal stream. This fixture does not price planner/model calls or establish wall-clock savings. GLOBAL_BLACKLIST is an intentionally unsound comparator, not a viable policy.

## Provenance and validation

- Frozen base main: 8d2eac460a7744d049bbca1d25b3cde86b1b496c.
- Candidate/auditor/image identities and the exact one-shot commands: FREEZE.json and PREREGISTRATION.md.
- Raw candidate: formal_01/RAW.json, SHA-256 c2bee302dff0f1c1dc74d13e6c70188c8d7bfacc90d356435588cd138dd8fe4f.
- Independent audit: audit_01/AUDIT.json, SHA-256 1f42c8391c3bf531b37033e0e49a1421b83e3a4a940d6f189f1b49105222fbda.
- Construction suite: 8/8 normal Python and 8/8 optimized Python before freeze, and repeated after the formal run; py_compile passed. These are not formal invocations.
- Analysis-index check exited 0 in sparse-checkout mode; it noted omitted sibling directories are not treated as removals.
- The analysis workflow archival-closure suite passed 3/3 tests, including CI sparse-selection coverage and retained #6611/#7418 contracts.
- Formal roles are never repeated. The frozen preregistration hard-break whitespace remains byte-identical; its hash verifies against FREEZE.json.

## Limits

All states, blockers, generations, expiries, proposals, and effects are authored symbolic data under a complete exact oracle. No screenshot-derived feasibility, real GUI, OS input, model call, action authority, production planner, human behavior, safety, latency, task benefit, or product capability was measured. In particular, this does not show that a real refusal reason is sound enough to prune a GUI plan; uncertain or unmodeled real evidence must remain UNKNOWN/YIELD.
