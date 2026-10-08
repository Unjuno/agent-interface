# Issue #5919 — post-merge raw-only audit review

**Disposition: `PASS_RAW_REVIEW`; no new scientific allocation or candidate run.**

This additive review preserves PR #5923's original report, fixture, candidate, outputs, and audit unchanged. It resolves one narrow evidence-quality question raised after merge: whether the original retained candidate output actually satisfies the frozen case contract, and whether altered output copies are rejected by a validator rather than only described in probe metadata.

## H / T / D / C / U

**H.** A separately authored validator over the frozen fixture and retained candidate result accepts the exact original output, rejects three actually mutated candidate-result copies, and rejects duplicate, missing, or extra result rows.

**T.** One post-merge raw-only audit was run at 2026-10-01 08:48:08 UTC in a fresh Codex V8 isolate. It consumed the exact GitHub blobs listed in `AUDIT_RESULT.json`. Candidate invocations: 0. The original result was cloned in memory, three frozen outcome fields were changed one at a time, and each clone was passed through the validator. Three further clones exercised duplicate/missing/extra row rejection. The frozen original bytes were not modified.

**D.** The original retained output agrees with all eight independently recomputed fixture outcomes: two benign PASS, five injected FAIL at the expected stages, and one ambiguous UNKNOWN. Recomputed baselines/aggregate lists match. All three actual altered candidate copies and all three structural coverage corruptions are rejected: 3/3 + 3/3. Result: `PASS_RAW_REVIEW`.

The original `audit.mjs` is narrower than its report wording suggests: its `corruptionsRejected` value compares fields in the candidate's `corruption_probes` metadata; it does not itself construct and validate those corrupted candidate copies. This addendum does the latter in a separate source/invocation. It does not change or retroactively relabel the original audit result.

**C.** All expected mappings and the `visual_proxy_similar` values are stipulated by the synthetic fixture. The reported visual-proxy miss is not an image measurement.

**U.** No candidate rerun, natural translation adjudication, real rendering, GUI/app, model, performance, safety, fairness, or broad multilingual-robustness evidence. This is a reproducibility/integrity review only, not a new H-pass.

## Provenance

- Original T0 merge: PR #5923, merge commit `15658ee8c942ec8a8af7613f8e3f6722a377da6d`.
- Audit input base: `ee0bf5670c4f9cec0c1de1a0e966eb3dd6566c15`.
- Exact fixture/raw/candidate/original-audit blobs and the new audit source are listed in `AUDIT_RESULT.json`.
- Frozen new source: `audit_review.mjs`, Git blob `9a81e043b7df6fb3372b2283f5e3006cd81aef6d`.
- Candidate invocation count 0; post-merge audit invocation count 1; retries 0.
- No Docker/container, GPU, model/provider, GUI, application, subprocess, or filesystem mutation was used.

The original PR's synthetic method result remains scoped to its eight authored records. A higher-fidelity successor would need independently adjudicated locale/effect traces and actual rendered evidence.
