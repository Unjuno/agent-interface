# Issue #5841 T2 — fixture-derived truth-label re-audit

## H / T / D / C / U

- **H:** Reconstructing each T1 row's truth labels from the frozen fixture, rather than trusting labels copied into candidate output, will detect truth-label corruption that leaves T1's reported rates and disposition unchanged.
- **T:** On current main `4d3c8d3612e3c57f354f5e1be553ae4f5a7801e0`, read only T1's frozen `fixture.json` and retained `results/candidate.stdout.json`. Independently enumerate the seven cases and eight assignment rows per case from the fixture. Reconstruct `ground_truth` and the intended observed record for each row, then compare case/row identity and every output summary. Run one raw-only audit, then five in-memory corruptions: flip one primary truth label; swap two primary truth labels while preserving their aggregate; flip a clean-case sentinel label; flip the true-collateral label; and delete the true-collateral sentinel label. The original T1 candidate, auditor, fixture, raw, and allocation are never changed or rerun.
- **D:** `PASS_FIXTURE_DERIVED_RAW` only if the retained T1 bytes conform to the fixture-derived rows and summaries and all five corruptions are rejected. Any unmutated mismatch is `FAIL_T1_RAW_LABEL_MISMATCH`; any accepted corruption is `FAIL_MUTATION_CONTROL`.
- **C:** The fixture and candidate encode the same finite synthetic design; an independent reconstruction can share a mistaken fixture assumption. This does not establish that a real benchmark scorer or export pipeline follows the model.
- **U:** Seven synthetic cases / 56 assignments only. No production scorer, live route, model, GUI, or #57 result is evaluated.

## Execution boundary

This is an audit-only successor on a separate branch/path. The T1 candidate is not invoked. The only formal invocation is one CPU raw-only auditor; the five corruption controls are in-memory unit-test mutations. No container, GPU, network, repository runtime, task input, or service is used.

Inputs are the byte-frozen T1 fixture copied from its original source commit and the retained candidate raw output in sibling `same_cohort_negative_control_5841_t1_v1/`. `FREEZE.json` binds the inputs, Git blob IDs, T1 freeze/source identity, current-main base, and this package's audit/test sources. The raw audit reads no T1 candidate or T1 audit implementation. Host working-tree line-ending conversion is explicitly excluded: the copied fixture bytes, not the converted T1 working-tree checkout, are the audited frozen bytes.

## Terminal interpretation

This can strengthen or qualify the retained T1 evidence only. It cannot repair, rewrite, or replicate T1, nor establish an empirical route effect or production bias-detection sensitivity.
