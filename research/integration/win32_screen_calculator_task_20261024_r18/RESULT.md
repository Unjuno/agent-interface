# R18 result — pre-input stop on visual-gate text mismatch

## Disposition: PRE_INPUT_STOP

The fresh UIA check read 1,044, and the same-session screen-physical image visibly showed Calculator at 1,044 with a valid target generation. The frozen runner prompt still named 1,043, so the visual confirmation gate contradicted the preregistered baseline. The attempt was aborted before dispatch; `call_count=0`, `input_dispatched=false`, and the observation-only session closed with no unresolved calls.

This is a runner construction stop, not task or action evidence. R18 remains unchanged and is not retried. The next runner derives its visual prompt from the frozen expected baseline to avoid this mismatch.
