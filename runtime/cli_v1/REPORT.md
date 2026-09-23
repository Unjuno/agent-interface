# Unified runtime CLI/API v1

Task `RUNTIME-UNIFIED-CLI-V1-20260917-001`, Issue #641.  
Immutable integration base `ae22793c3af86e3e6c82c954ca075b26c88d1df7`.

Decision: **`PASS_UNIFIED_RUNTIME_CLI_V1`**.

The CLI/API adds no execution semantics. `doctor()` reports the fail-closed
`selector_v1` plan and keeps `side_effect_authority=false`. `dispatch()` accepts
an already-authored program plus explicit native target registry and current
observation/binding values, opens only the actual-host promoted backend, and
passes the program/freshness values through unchanged to that backend session.

CLI surface:

```text
python -m runtime.cli_v1 doctor
python -m runtime.cli_v1 dispatch --program FILE --targets FILE \
  --current-observation-seq N --current-binding-revision N [--display DISPLAY]
```

Program and target JSON may be read from files or stdin (`-`). Output is exactly
one JSON record on stdout. Malformed JSON/backend-unavailable requests exit
nonzero and do not retry automatically.

GitHub Actions run `35128121080` passes on Ubuntu, Windows and macOS. Each job
passes compile, the combined CLI/API + selector tests, and a machine-readable
`doctor` invocation. The integration tests explicitly verify that dispatch
passes the same program object and supplied freshness values through without
rewriting them, and that malformed target registries fail before backend
construction.

Native effect semantics remain those independently promoted and tested in
`x11-v1`, `win32-v1` and `quartz-v1`. Wayland target discovery and automatic
permission escalation are not introduced here.
