# R32: restore close admission after an unentered close

Date: 2026-10-22

## Finding and correction

The current-main transplant in R31 reserved `shutting_down` before submitting
`interface_close`. That prevented a fresh close after the executor rejected
work before invocation, and blocked a later close receipt after a close worker
had already completed. The broad Native MCP workflow reproduced five such
close-retry failures. The fix rolls back the reservation only when worker
admission was revoked before callable entry and no server-lifespan shutdown
has started. A completed owner close remains retrievable.

## Validation

- Base: `e7c1c41dcf0f552fb85154d6905bd0820591ea81`, with the R31 source slice.
- Local environment: Windows, Python 3.11.9, Fake X. No WSL, WSLc, Xvfb,
  physical desktop, or provider.
- Focused supervisor/public-MCP suite: 116/116 passed in normal Python and
  116/116 under `-O` (`normal-focused.*`, `optimized-focused.*`).
- Five regression cases implicated by the Native MCP CI run passed in normal
  and optimized Python (`*-close-retry.*`).
- Source fingerprints for the seven implementation/test files are identical
  before and after the validation (`source-before.json`, `source-after.json`).
- All raw logs and exit codes are retained; `SHA256SUMS` covers every packet
  file except itself.

## Separate environment finding

The local Windows test `test_portable_stdio_runs_outside_checkout` still
errors before exercising this patch because `SOURCE_FILES` includes
`runtime/backends/win32_v1/__init__.py`, which is absent from the current-main
checkout. Its raw output and exit code are preserved separately in this packet.
This unrelated portable-stdio fixture issue is not folded into the supervisor
change. The Linux Native MCP job's earlier five failures were the close
reservation behavior above; this Windows-only missing-file error was observed
in a separate invocation.

## Reproduction

From repository root, run the four focused modules named in `conditions.json`
in normal and optimized Python, then the five test IDs listed there in both
modes. Check `portable-stdio-windows.raw.log` separately for the independent
missing-source-file finding.
