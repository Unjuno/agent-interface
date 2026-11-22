# Current-main Docker/Linux public MCP contract R01

## Freeze

- Main baseline: `d18eefdb558d8292649f235d61a22bcd5a4e1b53` (main was unchanged on first and last reads before this run).
- Runtime/test tree: exact current-main tracked sources mounted read-only at `/workspace`; working tree runtime tree was verified byte-identical to `origin/main`.
- Image: `issue57-calc-appserver-r88:local`, image ID `sha256:a3b2b4cd54ca731a86f8d2ba16f1eb833220122c60bfafbdb048e5ad39e50056`, created 2026-11-03. Python 3.11.2; import preflight passed for `mcp`, `Xlib`, `vizdoom`; Xvfb/Openbox/xauth present.
- Container network: disabled. Source mount read-only. Tests use their normal per-test temporary roots; no model/provider, GUI target, Docker sibling container, or WSLc allocation is invoked.
- Target: `runtime.cli_v1.test_mcp_server` + `runtime.cli_v1.test_mcp_guarded`, local/CI MCP contract modules.
- Modes: normal and optimized (`-O`), no retry or dependency installation.
- Output: raw stdout/stderr and exit codes retained in `raw/`.

## Pass rule

Both module groups must pass in both interpreter modes. A pass qualifies only the frozen local public-MCP contract on this Linux image; it does not qualify live GUI control, task effect, provider accounting, recovery reliability, MAP01, Research Preview, or runtime distribution acceptance.
