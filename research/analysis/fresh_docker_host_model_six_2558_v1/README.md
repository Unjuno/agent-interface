# Fresh six-allocation Docker/host-model result (#2558)

Six independent Docker X11 allocations used the PC-local `codex.exe` bridge.
Five model outputs passed the compiled grounding and geometry gates and all
five produced the exact independent effect `saved=true, text=docker2558`.
The sixth model output was rejected by the validator because field and submit
coordinates collided; it was not retried and emitted no native action.

Every admitted run verified release. Every focus-change reuse probe returned
`SCOPE_MISMATCH` with zero extra emissions. This is a six-allocation fixture
result, not a general GUI reliability claim.
