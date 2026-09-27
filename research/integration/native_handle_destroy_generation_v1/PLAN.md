# Issue #4242 plan

H: exact bound-surface DestroyNotify can advance one caller generation through the existing NativeHandleBridge review/rebind boundary, revoking old aliases before native input while preserving a fresh replacement alias.

T: execute the exact current-main NativeHandleBridge from repository checkout on four fresh private Xvfb/Openbox sessions. Three cases per session: stable fresh consequential click; same-XID/same-pixel replacement static diagnostic with zero input; same replacement plus explicit destroy-generation review, old-alias zero-input refusal, then one fresh consequential click. One formal workflow invocation, no retry/replacement/tuning.

D: PASS only for 12 complete rows; stable/fresh candidate effects exactly once with verified release; static diagnostics expose old eligibility but emit zero; candidate DestroyNotify advances binding revision/scope exactly once, old alias refuses before emission/effect, fresh alias succeeds; terminal input and Xvfb/Openbox cleanup clean; independent audit and >=8 corruption controls pass.

C: explicit review_window is caller-driven; no automatic runtime watcher or public CLI integration, check/use atomicity, arbitrary-app, model, token/latency, or product claim.

U: production lifecycle plumbing and matched #2789/#3311 six-task evaluation remain open.
