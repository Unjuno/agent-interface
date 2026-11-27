# Compiled Win32 recovery obligation projection (2026-11-14)

## Finding

The retained native R180 `interface_results` row has `standard_program` and the exact cancellation receipt, but its nested `action` omits the redundant `obligations` field. Before the fix, passing that row directly to the current compiled Win32 caller returned `status=uncertain` and `release.verified=false`, even though the cancellation receipt held `obligations=["button:map01:left"]`, a recovered status, a matching generation/readback, and a returned `button_up` attempt.

The caller now re-derives obligations from `standard_program` only when the action field is absent. It requires the program schema, a source target-generation mapping containing the expected generation, successful derivation, and exact equality with the cancellation receipt. A changed button in the program, stale generation mapping, absent program, malformed derivation, or contradictory present action obligations keeps the result uncertain. Source action outcome stays UNKNOWN; the caller reports `delivery_uncertain`, retains `input_dispatched=true`, and never upgrades task success.

## Evidence

- The unmodified retained R180 `dispatch-terminal.json` was evaluated with `_terminal()` before the patch: `uncertain`, `release.verified=false`.
- The same retained row after the patch: `delivery_uncertain`, `release.verified=true`, `input_dispatched=true`.
- A focused constructed projection with a left-button program and matching cancellation obligation passes; a right-button program or stale generation mapping fails closed.
- `runtime.cli_v1.test_supervised_win32_compiled`: 8/8 passed normally and 8/8 under `python -O`.
- `runtime.cli_v1.test_mcp_supervised_win32`: 32/32 passed normally and 32/32 under `python -O`.

These checks validate caller receipt composition and fake-backed stdio integration. The R180 fixture is retained evidence, not a new GUI run. They do not establish a fresh live recovery, task effect, broad reliability, matched Issue #57 efficiency, or completion of computer control.
