# Exact-source regression follow-up

## H / T / D / C / U

**H.** The merged #7471 scorer-attribution candidate can misclassify a progress change already observed before first input when it selects the first post-acceptance sample as baseline. The successor policy in this PR should reject the same history by using the freshest pre-input sample.

**T.** One deterministic fixture was run against the exact candidate blob from current main `b47d4d0b053f6e7d88c37e24be81777aa28feb6a` and the successor candidate. Sample history is `(105,0),(110,0),(115,1),(130,1)`; accepted time is 100 and first input time is 120. The 115 sample already observes the kill before input; the 130 sample merely repeats that count.

**D.** The merged function returned `ADMISSION_BRACKETED_PROGRESS` with baseline 105 and positive sample 130. The successor returned `POST_CANCELLATION_COOCCURRENCE` with `no_bounded_post_input_progress`. The old source Git blob was independently confirmed as `3a097172115b6d8c2cd482c37c80388b86404b25`, and the raw-only audit passed. Four focused tests now pass, including the paired prior-versus-successor regression. See `followup_raw.json`, `followup_audit.json`, and `FOLLOWUP_SHA256SUMS.txt`.

**C.** Local deterministic policy comparison only, on Python 3.12.13/macOS arm64. No container retry, game, model, live input, or allocation occurred. This follow-up does not alter the frozen seven-case predecessor result.

**U.** The false classification is demonstrated for this exact synthetic history; no runtime episode or actual scorer JSONL was parsed. The corrected label remains interval association, not causal attribution. Live useful recovery and MAP01 completion remain unverified.
