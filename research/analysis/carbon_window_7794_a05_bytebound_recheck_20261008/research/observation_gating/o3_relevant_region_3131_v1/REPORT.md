# O3 live source-window binding experiment

- Issue: #3131
- Image: `agent-interface-2994:20260920`
- Image digest: `sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c`
- Execution: fresh Docker container, `--network none`, Xvfb `:146`, real GTK fixture
- Actual X11 window: `2097155`
- Raw transport result: `FAIL_RELEVANCE_ESCAPE`; the unmodified evaluator admitted forged `source_window=9999999`.
- Successor verifier result: `PASS_O3_SOURCE_WINDOW_BOUND_SCOPED`.
- Scope: source-window binding only; no model calls, no broad GUI task success, and no two-application generalization.

The original failure is preserved in Issue #3131. The verifier is additive and rejects the forged case before evaluator admission.
