# R19 result — scoped integrated Calculator task PASS

## Disposition: PASS_SCOPED

One same-session public `screen_physical_px` observation returned a nonblank 320×533 Calculator image showing 1,044. After visual inspection at the frozen gate, one dispatch was issued: call `4e4b4cee1a0a4f41be6642cbba9e90bc`, operation `fb5d8156604d490d8ed3ec8df313ce64`, target generation `6c8471d23316dfac526a53a0249470c0289b6744ab2124b19b24df8d9f321c7c`. The action completed, and independent UIA reads show 1,044 before and 1,045 after.

The configured task verifier accepted one exact seven-field certificate bound to the same call, operation and generation. `interface_verify_task` returned `verified` with `task_success=true`; retained results agree. The dispatch release receipt reports no held or unknown keys/buttons and `verified=true`; completion custody records a neutral readback on the same operation and generation. The call was not replayed. Session close completed with no unresolved calls. The close operation itself reports `release_confirmed=false`, which is expected because the separate completed action already owns the verified release/readback evidence.

## Scope

This is one native Windows Calculator sample using screen-physical observation and a configured UIA oracle. It does not establish WSLc behavior, MAP01 control, blocked-I/O recovery, matched efficiency, or broad reliability. R15 remains the black `window_client` capture plus skipped-verifier HOLD; R17 remains the rejected-extra-fields HOLD; R18 remains the pre-input prompt-mismatch STOP. No historical attempt was retried.

`audit_r19.py` rechecks the frozen manifest and reproduces the result from raw wrapper, image, UIA, oracle, release, readback and close receipts.
