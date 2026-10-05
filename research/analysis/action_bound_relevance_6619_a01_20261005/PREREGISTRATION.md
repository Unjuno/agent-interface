# Preregistration: Issue #6619 task relevance successor A01

This is a new synthetic method cohort for the 2026-10-03 Issue #6619 evaluation addendum (`FREEZE.json` pins its exact comment). It does not reuse #6632 input rows or outputs. Current main is pinned at `190100f7c9acb2bfc5618d1621761a0329b368eb`.

- **H:** A prediction-only suppressor will suppress correctly predicted but task-required evidence; a complete-relevance gate will preserve all required and hard-critical cues, meet declared delivery deadlines, and suppress at least one optional matched cue. Candidate-visible pixels, receipt and prediction cannot identify the scorer-only causal origin of yoked frames.
- **T:** One no-model/no-GUI deterministic run over the eight SELF/EXTERNAL × MATCH/MISMATCH × REQUIRED/IRRELEVANT rows, plus hard-critical and unknown-receipt/coverage controls. Compare full-frame, prediction-only and the exact pinned #1726 `COMPLETE_ONLY` implementation. Candidate code imports that byte-pinned function. One independent raw-only auditor reconstructs all rows and tests four mutations. Oracle is separate from candidate input. Host standard-library Python is used because #6619 does not authorize a container allocation.
- **D:** See `FREEZE.json`. Exact gates are fixed before candidate run. Candidate is invoked at most once; auditor once after candidate exit zero; retries=0.
- **C:** Full-frame or the existing #1726 complete-relevance gate may dominate; finite synthetic cases do not demonstrate a useful visual predictor.
- **U:** Relevance/completeness are trusted fixture inputs; actual source-bound input, runtime delivery, image semantics, game safety, task effect, benefit and Issue #59 live acceptance remain untested.
