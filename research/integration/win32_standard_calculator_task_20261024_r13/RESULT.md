# R13 result — observation stopped on out-of-bounds capture

## Disposition: PRE_INPUT_STOP

The public `interface_observe(window_client)` request used `[0,0,336,541]`, inferred from the outer window. Read-only Win32 geometry showed the actual client was 320×533. The API returned `observation_failed` with `capture outside client bounds`; it returned no generation and dispatched no input. UIA still showed the precondition value 1,042. The session closed with zero calls and no unresolved call IDs.

This corrects the initial handoff hypothesis: the parser did not reject a valid generation; none was returned. The later R15 corrected bounds and found a separate all-black capture issue.
