# Public owner pre-dispatch hook wiring (2026-11-15)

## Change

Candidate commit `25edfca74ed3da752ae8f2f233e22ed010be6417` adds the
registered-runtime `before_action_dispatch` callback to
`GuardedSessionOwner.run_compiled`, validates it as callable, and passes it to
the existing compiled graph. The public MCP request schema is unchanged and
does not accept callbacks. This supplies the owner-wrapper link needed for a
trusted registered profile to retain per-action pre-dispatch evidence.

The regression uses the actual compiled graph and guarded X11 adapter over
Fake X. It verifies both dispatch receipts join to the corresponding completed
transition action IDs; a first-action guard refusal yields no dispatch receipt
or input; and a second-action refusal yields exactly the first action's
receipt. The test clock pins `monotonic_ns` and `perf_counter_ns` to one
virtual monotonic clock so cross-layer timing assertions use the same domain.

## Verification

Environment: CPython 3.11.9, Windows. Source base:
`791d1afafacd18eb6714644047ffc759dc726d42`.

Commands and results:

```text
python -m unittest runtime.cli_v1.test_mcp_guarded
Ran 56 tests in 14.144s — OK

python -O -m unittest runtime.cli_v1.test_mcp_guarded
Ran 56 tests in 13.379s — OK

git diff --check
OK
```

Raw output: [`public-owner-normal.log`](public-owner-normal.log), SHA-256
`CCBAABB52D20C60D5145E813AB5FF59094FCD1380AD31C55952D8964CC7E270C`; and
[`public-owner-optimized.log`](public-owner-optimized.log), SHA-256
`50BD4DFA9D42FA89C32B793572F892BAE961BB04FD5005E08EDDD67E66932C52`.

Changed-source SHA-256:

| File | SHA-256 |
|---|---|
| `runtime/cli_v1/mcp_guarded.py` | `0FB1E48661B35DC49DCA083A1B3852A77F342C224304421EFA4C2A1D2E49ED99` |
| `runtime/cli_v1/test_mcp_guarded.py` | `2AD896B3ACA9FA8B1F42C91CA8105D02C7EE0FEE1F5692FB6EA963CA97623986` |

## Limits and next connection

This is wrapper/caller composition evidence only. The graph and input path are
Fake X; no Calc application or live GUI was used. The public G10 profile is
still unregistered. This change does not implement G10 action semantics,
two-save preparation/receipt custody, post-close scoring, native Win32
recovery, MAP01 effect, or #57 efficiency. Next code step is to add the
trusted callback to the G10 registered profile, mint its save request from
the pre-dispatch receipt, snapshot only after the matching release-verified
action, and plumb both records through the parent verifier.

The pre-existing focused logs in this directory remain unchanged and preserve
their original test scopes.
