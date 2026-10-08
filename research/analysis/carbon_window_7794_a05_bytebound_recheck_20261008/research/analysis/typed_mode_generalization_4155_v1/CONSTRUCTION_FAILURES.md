# Construction failures and corrections — Issue #4844 v1

This is a chronological record of preformal construction. None of these attempts used formal allocation seeds (support 415571–415573; held-out 415581–415583), and none is formal scientific evidence.

1. Initial scoring conflated a low-confidence fallback YIELD with a model's correct YIELD disposition, which obscured safe abstention versus wrong emitted recovery. Corrected the report metrics to distinguish wrong non-YIELD recovery, safe recovery coverage and unnecessary YIELD.
2. With support 48/mode and confidence gate 0.65, the contradictory all-ones control produced an unjustified actionable disposition. The control caught the issue. Support was raised to 96/mode during construction only; formal sample count is now frozen at 96 and no formal observations have been examined.
3. After changing support count to 96, the independent audit still regenerated 48/mode and rejected the test fixture. Auditor schedule was corrected independently; a later construction test verified exact agreement and prediction-corruption rejection.
4. Latest local Docker construction suite: 6/6 PASS. No formal allocation has run.
5. One PowerShell pilot invocation expanded an empty drive-mount prefix and Docker rejected `:/src:ro` before container creation. No data/output was produced. Corrected by composing the mount from the current location; the same pilot then ran inside local Docker and the independent audit returned `HOLD_MIXED_PARTIAL_RESULT`, `errors=[]`.

These corrections and their order must remain visible. They are not silently erased by the final construction pass.
