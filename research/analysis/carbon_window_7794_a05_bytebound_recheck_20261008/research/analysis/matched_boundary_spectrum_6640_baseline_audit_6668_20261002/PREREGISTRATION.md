# Preregistered archive audit — Issue #6668

## H / T / D / C / U

- **H:** Standard omitted baselines may materially reduce the apparent advantage of the matched boundary spectrum on the predecessor's finite synthetic fixture.
- **T:** Read only #6640 allocation-01 fixture, hidden-fault table, candidate raw, and audit. Per seed compute Ochiai \
  `ef / sqrt((ef + nf) * (ef + ep))`, raw failed-exposure count `ef`, and raw failed-exposure rate `ef / (ef + nf)`; also independently rebuild matched, unstratified, first-symptom and deterministic-random baselines. Missing exposure is neither exposed nor unexposed. Use descending score and lexical tie-break; unestimable scores sort last. Keep post-failure `render` in the diagnostic universe. Report MRR of the first active injected fault and fraction with every active injected fault in top two.
- **D:** `PASS_ARCHIVE_RECONSTRUCTION` only if all 8,192 unique rows, 32 seeds, active fault IDs, per-seed attempt digests, old per-seed scores/ranks, and four old aggregate metrics reconstruct exactly (float tolerance `1e-12`). Mismatch is `HOLD_AUDIT_INTEGRITY`. There is no new scientific threshold and the predecessor `FAIL_METHOD` cannot be changed.
- **C:** Alternative exposure normalization, tie-breaking, or removal of the post-outcome `render` symptom could change ranks; none is silently substituted.
- **U:** The same authored simulator, hidden fault injection oracle, and 32 seeds are reused. Post-hoc comparator analysis cannot establish behavior on independent data, causality, or operational inspection utility.

## Immutable inputs and limits

Successor Issue #6668 comment #5950821300 preregistered the comparator formulas and input set before the analytic output. Input blob identities were compared at the stated base and later main commits; see `INPUT_MANIFEST.json`. This is a post-hoc archive-only calculation: no old candidate/auditor execution, model, GUI, container, resource request, or new threshold. The audit code itself was not content-hash frozen before the first exploratory invocation; this is disclosed as a construction/provenance limitation, not a container/formal result.
