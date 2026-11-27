# Compiled X11 guard perception

Problem: one trusted perception callback serves both graph observations and every input dependency check. Expensive effect OCR can exhaust the native guard lease even when the guard needs only target identity.

Design: add optional keyword-only `guard_perceive(native, image)` to `runtime.guarded_x11_v1.compiled.run`. Default to `perceive`, preserving behavior. When explicitly supplied, call it only during native input guard checks, on copied fresh native evidence and image. The existing association checks, declared identity/dependency predicates, exact True requirement, deadline, input guard, evidence retention and failure semantics remain unchanged. Graph observation and effect callbacks continue to use `perceive`. Both callbacks are trusted caller code: the API does not validate the semantic truth of supplied predicates or justify constant `ready` values. No authorization, lease extension, retry, recovery or performance guarantee is added.

Steps: (1) Add failing tests for callback separation, false/missing guard values, and malformed optional callback; (2) implement the optional callback with default fallback; (3) run adapter and core tests, including optimized Python; (4) independently review and validate a fresh live Calc run separately before claiming practical benefit.

## Post-release observation settling candidate

Provide an opt-in bounded fixed wait only after a completed action and verified neutral release, outside the input guard. Share the core method deadline starting at its first clock sample, poll cancellation in small intervals, preserve the terminal and let the core report cancellation or budget expiry before any further action. If cancellation checking is invalid or raises, stop waiting and let the core fail closed. Default zero preserves current behavior. A wait is not evidence of an effect; a fresh observation and effect verifier remain mandatory. A fixed delay is not event-based readiness or a hard OS scheduling guarantee. Test normal completion, cancellation after release, failed release and invalid parameters before live use.
