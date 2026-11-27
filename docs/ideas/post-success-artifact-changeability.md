# Post-success artifact changeability

- **Source:** Open [Issue #6610](https://github.com/Unjuno/agent-interface/issues/6610); finite synthetic result in merged [PR #6614](https://github.com/Unjuno/agent-interface/pull/6614).
- **Duplicate disposition:** [Issue #8578](https://github.com/Unjuno/agent-interface/issues/8578) proposed a closely related verified correction-cycle assay and was closed as a duplicate of #6610. Its explicit discrepancy/new requirement and separate diagnosis/localization measures are possible refinements to #6610's protocol, not an independent hypothesis or result.

## Question

When two routes produce an artifact that satisfies the same initial task contract, does preserving native structure reduce the cost of a later, explicit change request enough to offset its initial cost? Editability is not an unstated requirement of the initial task. If no later change occurs, or a flattened representation is simpler to revise, structure may add cost without value.

## Evidence

The merged T0 is a finite, hand-authored synthetic assay over six spreadsheet/drawing cases. Its independent auditor reported 35 checks and rejected all five corruption controls. The declared operation-cost ranking favored flat output for initial work, then favored structured output under the illustrative 0.4/0.4/0.2 follow-up mixture; the no-follow-up and raster-patch strata favored flat output. These integer operation costs are not elapsed time or real user effort.

The exact candidate and auditor JSON are not stored as Git bytes. Their SHA-256 hashes and the execution limits are recorded in the retained [result](../../research/analysis/post_success_artifact_changeability_6610_t0_v1/RESULT.md). The result supports method sensitivity on synthetic fixtures only. It does not show real-application editability, user preference, model behavior, or product benefit.

## Scope for any continuation

Keep #6610 as the sole owner of this question. A future assay can separately record correction detection, diagnosis, localization, edit actions, total correction-request-to-verified-result cost, and preservation of unaffected requirements. Freeze the later change request independently from initial acceptance, count every offered attempt, and independently verify both initial and corrected effects. Include no-follow-up, flat-is-easier, ambiguous/UNKNOWN, collateral-edit, and missing-dependent-update controls. Do not treat a synthetic method pass as evidence about real correction frequency or user benefit; any native-app or participant study needs its own scope, authorization, and review.
