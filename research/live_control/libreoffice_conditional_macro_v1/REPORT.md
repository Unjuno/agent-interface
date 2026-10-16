# LibreOffice cooperative conditional macro v1

## Result

`PASS_COOPERATIVE_CONDITIONAL_CALL_SCOPED`.

Ten frozen first cases completed on LibreOffice Draw 25.2.3.2.

- `macro_stable`: 5/5 application-hosted Python macro returned `APPLIED`, moving named A from x=1000 to x=1200; B remained 5000.
- `macro_stale_before_call`: 5/5 a separate UNO client first moved A from 1000 to 1700; the identical macro invocation with `expected_x=1000` returned `REFUSED` and left A=1700/B=5000.
- Independent audit passed all rows with zero errors and verified frozen source hashes, schedule, external-before-macro ordering, macro return and final geometry.

This establishes only a cooperative application-specific conditional-call boundary for state that is already stale before invocation. It does not prove that a concurrent external UNO mutation cannot interleave after validation while a long-running macro invocation is in progress. That is the next single question.
