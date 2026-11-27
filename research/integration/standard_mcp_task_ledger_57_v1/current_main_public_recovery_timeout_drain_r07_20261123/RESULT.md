# R07 result: second diagnostic harness failure

Disposition: **FAILED_TEST_DESIGN** in both modes (exit 1); no retry was made.

- Normal mode: the 3-second event-start guard expired before the fake observer reported ready. This guard was too short under the observed host scheduling; the callback timeout path was not exercised in this sample.
- Optimized mode: the caller timeout and event release proceeded, but `self.row()` intentionally unwraps the observation receipt and drops the surrounding call ID. The test compared the unwrapped raw receipt against a call ID and failed. The exact-call readback path was therefore not scored.

The source design is corrected for a separate R08 attempt: use a finite 20-second startup guard and inspect the full `interface_results` envelope for `call_id`. R06/R07 remain preserved as distinct harness-design failures. They do not establish or refute product callback cleanup behavior.
