# Compiled X11 guard perception

Problem: one trusted perception callback serves both graph observations and every input dependency check. Expensive effect OCR can exhaust the native guard lease even when the guard needs only target identity.

Design: add optional keyword-only `guard_perceive(native, image)` to `runtime.guarded_x11_v1.compiled.run`. Default to `perceive`, preserving behavior. When explicitly supplied, call it only during native input guard checks, on copied fresh native evidence and image. The existing association checks, declared identity/dependency predicates, exact True requirement, deadline, input guard, evidence retention and failure semantics remain unchanged. Graph observation and effect callbacks continue to use `perceive`. Both callbacks are trusted caller code: the API does not validate the semantic truth of supplied predicates or justify constant `ready` values. No authorization, lease extension, retry, recovery or performance guarantee is added.

Steps: (1) Add failing tests for callback separation, false/missing guard values, and malformed optional callback; (2) implement the optional callback with default fallback; (3) run adapter and core tests, including optimized Python; (4) independently review and validate a fresh live Calc run separately before claiming practical benefit.
