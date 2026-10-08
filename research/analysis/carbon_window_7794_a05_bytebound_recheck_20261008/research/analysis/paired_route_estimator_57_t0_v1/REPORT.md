# Issue #57 — paired all-attempt estimator T0 report

## Result

**METHOD_PASS_SCOPED** for the frozen synthetic ledger. GitHub Actions run
[36830781573](https://github.com/Unjuno/agent-interface/actions/runs/36830781573)
executed the candidate once and independent auditor once in separate Docker
containers; both exited 0. The auditor reconstructed all 3 scenarios, all 7
pair IDs and all 14 assigned arm attempts, and accepted 7/7 mutation controls.

| Synthetic scenario | Assigned pairs / attempts | Paired observed difference (integrated − baseline) | Interpretation |
|---|---:|---:|---|
| True null | 2 / 4 | 0 tokens; 0 ms | Correctly preserves the null |
| Planted benefit | 2 / 4 | −20 tokens; −200 ms | Recovers the hand-planted per-pair difference |
| Route-dependent FAIL/UNKNOWN | 3 / 6 | Observed-complete pair only: +5 tokens; +10 ms | `HOLD_INCOMPLETE_OR_SAFETY`; one pair has both endpoints |

The failure scenario demonstrates why survivor-only or unpaired observed-case
summaries can be misleading: observed arm means imply −7.5 tokens / −95 ms for
integrated, while the only complete same-pair difference is +5 / +10. All
three pair IDs and six assignments remain present; missing endpoints remain
null, not zero. The hard safety/effect gate fails because the scenario includes
FAIL, UNKNOWN and unverified outcomes. Neither summary is a route-effect
estimate.

The analyzer retains all-attempt arm totals, raw outcome/endpoint sequences,
exact same-pair links, paired differences and unpaired sensitivity summaries.
The auditor independently checks counts, identity links, endpoint values,
paired and unpaired summaries, and safety dispositions. No post-treatment
adjustment was performed; `repair_count` adjustment and relabeling it as
pre-treatment are rejected.

## Execution evidence

Allocation `57-PAIRED-LEDGER-T0-20261001-01`, run number 1 / attempt 1, frozen
event SHA `725d37c979f7d4dbdc348bbcbfedf0f3023a84f7`, publication base
`da7770df8bd896738a8a7e0ccc8ea45e10b3e645`. GitHub-hosted runner Docker Engine
was 28.0.4. Separate linux/amd64 containers used
`python:3.12.14-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`,
network none, read-only root, 128 MiB, 1 CPU, pids 32, cap-drop ALL, and
no-new-privileges. Both exited 0 with OOM false. Raw candidate JSON SHA256 is
`e74c5dcafd6d2a10ab399bd65ce934f567a24717bdb2662512070defcd6f1956`; it
matches the runner's `SHA256SUMS` and was independently recomputed from the
GitHub content API bytes.

Raw candidate output, auditor summary, runner/image identity, container
inspection and start-gate record are retained under
`results/57-PAIRED-LEDGER-T0-20261001-01/`.

## Limits and next step

This result verifies only a small hand-authored estimator fixture. It does not
validate real task pairing, independent reset integrity, order/carryover,
missing-outcome assumptions, covariate-adjustment assumptions, live task
effects, safety, actual model token accounting, cost or end-to-end speed. The
observed-complete pair summaries are shown with their denominators and must not
be generalized across missing rows. Keep #57 open; before any interpretation
of a future integrated comparison, reconcile the separate current-main
plan-versus-frozen-decision mismatch already recorded on the Issue, then verify
pair/order/reset integrity and report paired and unpaired uncertainty without
dropping failures or relaxing the safety gate.
