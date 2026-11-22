# Live caller to effect handoff seam — R01

## Conditions

- Source base: current main `cf66c1758f25a0beafe8d577502bd849dcd6e2cf` plus the candidate changes in this PR.
- Runtime: Windows CPython 3.11.9.
- Suites: `test_effect_receipt_handoff_v1`, `test_recorded_comparison_adapter_v1`, `test_comparison_measurement_v1`.
- Synthetic Fake Relay and research adapter only. The standard `RecordedPublicMcpCaller` and `ProviderAttemptRecorder` execute; no OS GUI, external provider, MAP01, Docker, or WSLc is used.
- Raw stdout is base64 encoded to preserve exact bytes through Git. See `RAW_OUTPUTS.md` and `SHA256SUMS`.

## Result

- Combined adapter suites: normal 47/47; optimized (`python -O`) 47/47.
- The standard caller records two local observations, `interface_dispatch`, `interface_results`, and a terminal independent-score event in one reconciled receipt.
- The measured-run adapter preserves action call ID, operation, target generation, owner lifecycle receipt and both observation links.
- The effect handoff joins the independent final score and separate before-state receipt to the same dispatch; the bounded effect interval is adjudicated `within_authority`, factual success is true, and eligible success is true.
- Wrong action-call identity is rejected. A one-capture run without its after-capture remains rejected.
- The comparison validator reads source sequence from the standard Relay response envelope, including request ID, SDK timestamps and next ID, as well as the existing direct fixture shape. A mismatched source sequence fails closed.

## Limits

This is finite synthetic transport composition with fixture owner and scorer receipts. It proves the offline caller journal-to-effect-adapter seam, not physical release, scorer independence, external-provider usage completeness, live GUI/MAP01 task success, matched integrated efficiency, repeated reliability, or Research Preview graduation.
