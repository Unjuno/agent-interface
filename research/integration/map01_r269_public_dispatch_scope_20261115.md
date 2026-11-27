# MAP01 R269 public dispatch scope follow-up (2026-11-15)

## Frozen source and preserved run

This read-only adjudication uses the R269 packet frozen against current main
`dedafadfca1f1322dc8d2fcab5f5049e6681350c` (tree
`98ddbecd2a651e8ec3347e48392db0ce14096002`). The packet and trial raw remain
local-only under
`D:\CodexData\Workspaces\2026-11-15-agent-interface-followup\r269-current-main-guarded-focus-expiry\trials\r269_native_guarded_focus_expiry_map01\`.
No frozen file was edited.

The public terminal row says outer `input_dispatched=false` and
`operation_invoked=false`, while the nested source action is `UNKNOWN` with
`input_dispatched=null`, `release_confirmed=false`, `task_success=null`, and
replay denied. Program-action lower bound is zero. Its separate automatic
cancellation is also `UNKNOWN`: both SHIFT-UP and LEFT-UP SendInput attempts
returned count 1, but completion readback is `not_attempted`, the late-input
horizon is zero, and release remains unconfirmed. No task effect was recorded.
These fields support a pre-task stop classification; the returned SendInput
counts do not prove release.

The frozen runner stopped with `ValueError: nested source action scope
mismatch` because its task-effect path required a dispatchable source action.
That abort hid the more precise outcome. New local helper
`map01_dispatch_scope_adjudication_v1.py` classifies this shape as
`NO_TASK_DISPATCH_RECOVERY_UNVERIFIED`, preserves the no-effect/no-replay
result, and rejects contradictory action, recovery, identity, or readback
fields. Applied read-only to the retained raw `dispatch-terminal.json`, it
returned that classification with errors empty, retained `release_confirmed`
false and `late_input_horizon_ns=0`, and listed the returned UP attempts
separately.

## Current custody boundary

The later exact public orphan-recovery request in the retained
`postrun-recovery` packet was already attempted once for source operation
`bb1c1f207e34407db20c28703713ae6a` and generation
`3b8643b98af224b9d63eff8fd424db0a7016127ef934bb8ef1e2209e8f393c6f`. It
returned UNKNOWN because exact-target foreground verification failed; release
was not confirmed, replay is denied, and its response requires a fresh
generation for any later target action. The durable custody record currently
reads `status=unresolved`, revision 888, with that pending operation and LEFT
plus SHIFT obligations. Do not retry the recovery or dispatch under that
generation. At the read-only host snapshot, GZDoom PID 41580/HWND 250546256
remained open and Windows Security/CredentialUIBroker owned the foreground;
the security UI was not touched. No new live input or recovery was sent in
this follow-up.

The current-main helper has `focus_target_before_release=true` on this path.
The candidate now has a regression test that injects a focus-refusal exception
and verifies `release_all` plus all global key-UP sends are skipped and the
helper closes. This keeps the fail-closed behavior explicit while the
foreground is unrelated; it does not solve the inability to release in that
state.

This is a runner/adjudication repair and one retained-run interpretation. It
does not establish release, a two-second neutral horizon, delayed-operation
exclusion, 50→49 effect, or task success for R269. A new live trial needs a
cleared custody state and a fresh target generation. R175's separate native
50→49 evidence remains unchanged.

## Verification

The new synthetic structural tests pass **5/5** under normal CPython and
**5/5** under `-O`; `py_compile` and `git diff --check` pass.
The full `runtime.cli_v1.test_win32_supervisor_helpers` module, including the
new focus-refusal test, passes **42/42** normally and **42/42** under `-O`.

- Normal log: `D:\CodexData\Workspaces\2026-11-15-agent-interface-followup\map01-dispatch-scope-adjudication-20261115.normal.log` — SHA-256 `6CE19FE5C6E39322CA0B13F5B467573E2EEEC70D41FBF64D3E414DDBE59845D6`
- Optimized log: `D:\CodexData\Workspaces\2026-11-15-agent-interface-followup\map01-dispatch-scope-adjudication-20261115.optimized.log` — SHA-256 `6CE19FE5C6E39322CA0B13F5B467573E2EEEC70D41FBF64D3E414DDBE59845D6`
- Win32 helper normal log: `D:\CodexData\Workspaces\2026-11-15-agent-interface-followup\win32-supervisor-helper-candidate-dedafad-20261115.normal.log` — SHA-256 `3D686391025588184FE43681589405257B605E6B8B4764300FF24CE843240CBD`
- Win32 helper optimized log: `D:\CodexData\Workspaces\2026-11-15-agent-interface-followup\win32-supervisor-helper-candidate-dedafad-20261115.optimized.log` — SHA-256 `8680C69831B2B0E24F7DC21C1FB4EE3844B70CEA3F492C2601C5585B5814D5F4`

Private raw SHA-256 values: `dispatch-terminal.json`
`1312F5782FE0115E9F8753782854B17740DDCF9ABEE07445880B8073F74EDAB0`;
`automatic-cancellation-receipt.json`
`705C02A1627C240476E1F7D5BE6618F6DBB3E814D0FF76AFA557503C0AE3C255`;
and `stop-or-error.json`
`8BA58CAFEB169195024B803DD8E1347FE5F791EC9D0B68BAAD1C4E5754D8C2D9`.
