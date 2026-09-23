# Mixed-app long-session construction gate

This additive path supports successor Issue #2499. It is only a construction
gate: it verifies that Inkscape, LibreOffice Calc, and Chromium can coexist in
one disposable X11 session and that visible windows are observable. It does
not establish the preregistered four-transition session, typed stale-capability
invalidation, effect safety, or cleanup audit.

The local Docker result on 2026-09-20 JST was:

```json
{"apps":[{"app":"inkscape","observed":true,"window_count":1},{"app":"libreoffice","observed":true,"window_count":1},{"app":"chromium","observed":true,"window_count":2}],"decision":"PASS_MIXED_APP_CONSTRUCTION_READY","display":":140","input_operations":0,"model_calls":0,"network_calls":0}
```

The next formal allocation must add per-window identity/binding records and
the single persistent session ledger before any input or task-effect claim.
