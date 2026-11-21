# Live caller to effect handoff seam — R01

## Conditions

- Source base: current main `cf66c1758f25a0beafe8d577502bd849dcd6e2cf`.
- Runtime: Windows CPython 3.11.9.
- Suites: `test_effect_receipt_handoff_v1`, `test_recorded_comparison_adapter_v1`, `test_comparison_measurement_v1`.
- Offline Fake X/research adapter only. No external provider, live desktop, MAP01, Docker, or WSLc.
- The final raw stdout files are base64 encoded to preserve exact bytes through Git. See `RAW_OUTPUTS.md` and `SHA256SUMS`.

## Result

- Focused handoff suite: normal 12/12; optimized (`python -O`) 12/12.
- Combined adapter suites: normal 45/45; optimized 45/45.
- The recorded caller journal builds a measured run retaining action ID, operation, target generation and one linked local observation.
- Handoff rejects an effect receipt whose action call ID differs from the public owner receipt.
- A one-capture run is refused because the second retained capture is absent. Existing positive hand-assembled handoff test remains separate; R01 does not claim a fully caller-generated before/after effect receipt.

## Limitations

The fixture supplies lifecycle phases, capture timestamp/image pin, native effect interval, and independent score certificate. ProviderAttemptRecorder preserves the supplied score but does not prove scorer independence. This is not live provider usage reconciliation, matched efficiency, repeated reliability, MAP01, or Research Preview graduation.
