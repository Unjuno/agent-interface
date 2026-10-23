# R21 result — standard-caller short-block recovery

R21 ran once on 2026-10-24 on the user-authorized Windows 11 Pro PC (build
26300, CPython 3.11.9), using source commit `6aa42d247b9c457ce0ef54d4f0b22a1f833db5d3`.
The frozen input-free preflight and source hashes passed. The run used one new
owned fixture, one public stdio-MCP dispatch, one cancel, and one injected
Q-down held in the probe-owned `WH_KEYBOARD_LL` callback for a 249.367 ms
post-cancel window. The callback forwarded the event on return. No WSLc or
Docker operation occurred.

The public cancel returned `pending` in 1.3704 ms. The callback returned at
monotonic `483054588546700`; the exact producer PID/creation-time was confirmed
exited at `483054588957200`. The injected Q-up reached the hook at
`483054596004700`. Public cancellation then reported `recovered`,
`release_confirmed=true`, `replay_allowed=false`, and `task_success=null` in
316.4537 ms from cancel start. A separate process later read the same target
generation, observed Q-up, and exited cleanly. No emergency Q-up was needed.
The exact R21 sentinel was clicked, saved, and independently read back; fixture,
hook, and foreground cleanup succeeded.

The frozen audit remains **FAIL_OR_UNKNOWN (8/10)**. Its two failures read
`callback_return_ns` from the callback snapshot captured just after the probe
released the hook; that snapshot preceded the callback thread's write of its
return timestamp. The timestamp is present in the final event row and final
`hook_stopped` record. The additive [supplement](audit_supplement.json) checks
those final records and passes 7/7. It leaves the frozen audit untouched and
records a **PARTIAL** disposition because the public retained report still has
`action.status=running` after the cancellation receipt reaches recovered, and
`interface_close` returns `closed` with `release_confirmed=false`. Runtime
`task_success` remains null. The task effect was saved before the cancellation
point, so this trial does not prove task continuation after recovery.

R21 therefore establishes one finite public cancellation/recovery receipt and
an independent same-generation Q-up after a 250 ms hook delay. It does not
establish a terminal action result, effect-after-recovery, release while the
callback remains blocked, a hard release deadline, MAP01, WSLc transfer,
efficiency, or broad reliability. Preserve R21 and do not replay it.

## Follow-up repair and validation

R21 exposed that the public dispatch worker returned on recovered cancellation
without persisting a matching terminal action receipt. `mcp_server` now records
action status `recovered` only when the cancellation and nested custody receipt
agree on operation ID, target generation, recovered phase, and confirmed
release. It leaves `input_dispatched` and effect unknown, `task_success` null,
and replay denied. A new synthetic public-MCP regression first failed on the
old `running` action, then passed with the repair. The existing unknown-custody
and close-drain regressions also pass.

Local validation on Windows CPython 3.11.9:

- `python -m unittest runtime.cli_v1.test_mcp_supervised_win32` — 9/9 passed.
- `python -O -m unittest runtime.cli_v1.test_mcp_supervised_win32` — 9/9 passed.
- `python -m unittest runtime.cli_v1.test_mcp_win32_backend_composition` — 5/5 passed.
- `python -O -m unittest runtime.cli_v1.test_mcp_win32_backend_composition` — 5/5 passed.
- `python -m unittest runtime.cli_v1.test_mcp_server` — 26/26 passed.
- `python -O -m unittest runtime.cli_v1.test_mcp_server` — 26/26 passed.
- `python -m unittest discover -s runtime/cli_v1 -t . -p 'test*.py'` — 594 passed, 8 skipped.
- `python -O -m unittest discover -s runtime/cli_v1 -t . -p 'test*.py'` — 594 passed, 8 skipped.

An initial package-unaware discovery command produced 2 failures and 5 errors
because `-s runtime/cli_v1` imported tests as top-level modules; relative imports
and child-process module lookup then failed. The package-aware `-t .` invocations
above are the successful full-suite checks. No remote CI result is required for
this local verification.
