# Issue #6442 A03 — preregistration and H/T/D/C/U

This is a fresh allocation after two preserved pre-candidate STOPs. It does not amend their freezes, results, or source history. Allocation A03 binds the corrected source copied in current `main` to the exact hashes in `FREEZE.json`; all candidate/auditor outcomes remain unobserved at this preregistration.

## H — hypothesis

On this frozen finite authored hierarchy schedule, a bounded soft revisit policy should recover at least 14/16 targets after partial first inspection or a same-source-epoch revision hint, while hard visited-branch exclusion recovers at most 2/16 and soft revisits no stable/complete branch. Any positive soft-minus-hard result is only a comparator result: if soft ties stateless, the experiment does **not** support a soft-specific advantage.

## T — test

- Freeze: current main `fa791fe937fb24245e785d9e22928b3f4a6a42ae`; nine exact source hashes in `FREEZE.json`; cached Python OCI image digest and observed `linux/arm64` platform; network disabled; 0.25 CPU and requested 512 MiB memory; source/input read-only and separate empty output binds.
- 32 deterministic fixtures × four policies (`stateless`, `hard`, `soft`, `exhaustive`) = 128 policy/fixture rows; max 12 events each. Strata: 8 stable/complete, 8 partial first inspection, 8 same-epoch revision hint, 4 no-target/ambiguous, 4 forbidden nonreversible edge.
- Run order, source, fixtures, policy set, comparator, thresholds, commands and one-shot budgets are frozen in `FREEZE.json`. Construction once; candidate once; raw-only independent auditor once only if candidate exits zero; retries zero.
- Raw candidate bytes are the sole audit input. The auditor checks exact row/event reconstruction, all-policy summaries, observations before target claims, epoch invalidation, safe traversal, and six distinct corruption controls.

## D — decision

`PASS_METHOD_SCOPED` only if all 128 pairs/events reconcile, no forbidden traversal/false target/stale memory is accepted, the six mutation controls reject, soft reaches >=14/16 partial/revision targets, hard reaches <=2/16, stable soft revisits are zero, and audit errors are zero. The report must show all four policies and all three soft-minus-baseline contrasts; it must explicitly deny a soft-specific advantage if stateless ties or exceeds soft. Any unmet clean threshold is HOLD; integrity/safety defect is FAIL/STOP. No retuning, threshold changes, retries, or outcome pooling.

## C — confounders and alternatives

Labels, saliency, revision cues, costs and hidden transitions are authored. The schedule intentionally creates a setting where a no-revisit policy can fail. Stateless ranking may obtain the same result as soft revisit with less state; exhaustive search may fail under the event budget. This assay cannot estimate natural GUI frequencies, observation noise, latency, or task benefit.

## U — uncertainty / exclusions

One deterministic finite synthetic policy set on one OrbStack ARM64 environment. It does not establish LLM/model benefit, unfamiliar live GUI transfer, general search optimality, runtime authority/safety, real-world cost reduction, or product performance. The earlier A01/A02 STOPs remain historical records; this new allocation is not a rerun of a consumed candidate because neither predecessor launched candidate or auditor.
