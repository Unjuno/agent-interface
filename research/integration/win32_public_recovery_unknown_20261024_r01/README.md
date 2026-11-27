# Public Win32 recovery failure custody — R01

This synthetic checkpoint closes one failure-path gap in the guarded Win32
public MCP composition. It drives bind, admission, producer start, cancel, and
`interface_results` through the actual public route. The gated producer leaves
the fake CTRL state down. The spawned recovery helper then returns a receipt
for a different operation. The owner retains the action/cancellation record
as UNKNOWN; release confirmation and cancellation task success remain unset,
replay stays denied, the independent observer is not invoked, and the fake
DOWN state remains visible. The test records one producer factory call.

The same verification exposed a target-generation classification edge: after
the Win32 per-HWND cookie was added, a changed GUI-thread identity caused
`Win32BackendError` while reading the cookie. Public admission failed closed,
but returned the exception text instead of the stable
`TARGET_GENERATION_CHANGED` code. The adapter now normalizes a failed
generation reread to that code. Its public caller regression uses an explicit
integer fake `GetPropW` value, matching the Win32 HANDLE contract.

The first broad run exposed a test-fixture defect: an unconstrained `Mock`
returned another `Mock` from `GetPropW`, and `ctypes.cast` recursed until
Windows terminated Python with `0xC00000FD`. The faulthandler raw is retained.
With the fixture corrected, the five-test backend composition module and the
51-test combined caller/backend/owner/supervisor suite pass in both normal and
optimized Python. Raw outputs include the initial incident and successful
runs.

All helpers and state transitions here are synthetic. This packet does not
qualify native blocked `SendInput`, physical release, a hard release deadline,
live task effect, MAP01, WSLc, matched efficiency, or reliability.
