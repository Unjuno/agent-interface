# Win32 producer-exception result query on current main — 2026-11-16

## Source and environment

- Main commit: `92aede657e8fd221bd2d56b31e9cac74ffcbf7cb`.
- Windows, CPython 3.11.9.
- Scope: production MCP stdio with synthetic producer/supervisor fixtures; no native input was sent.

## Verification

Three exact public-stdio cases were run together:

1. `test_production_stdio_orphan_recovery_pending_exact_query`
2. `test_stdio_exception_unknown_then_fresh_generation_recovery`
3. `test_stdio_exception_auto_recovers_and_keeps_action_unknown`

Normal mode: 3/3 passed (28.466 s). `python -O`: 3/3 passed (28.001 s). Complete output is preserved in `raw/normal.log` and `raw/optimized.log`.

The cases cover recovery-call identity while pending, unrelated-call isolation, exact `interface_results` lookup, preservation of producer-exception source custody as UNKNOWN with release unconfirmed and `task_success=null`, separate recovery receipt with bounded late-input horizon, replay denial, and a distinct fresh-generation attempt whose task oracle is bound to its own dispatch call. The automatic-recovery response also retains the difference between outer recovery status and nested UNKNOWN source action.

## Source hashes

- `runtime/cli_v1/test_mcp_supervised_win32.py`: `6df44b738033f3a2c86e51b6d872230d821c976f26ae283b5d697a75730d365e`
- `runtime/cli_v1/owned_guarded_session.py`: `b84f8be9b1476d9f9d3a9d1e345952627ae1a77356df1339343c78e923428b45`
- `runtime/guarded_win32_v1/process_cancellation.py`: `6f953b9070f9e07e3fad4b775059f1cce91c17e4ec60a78d6b9694eb0577fd45`


## Limits

These are synthetic protocol/caller integration checks. They do not prove native Windows input release or a new MAP01 effect, and they do not establish #57 matched token, latency, or efficiency results. Historical R175 evidence and unresolved R269 custody are not modified or replayed.
