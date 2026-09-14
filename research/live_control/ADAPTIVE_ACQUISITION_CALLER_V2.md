# Adaptive acquisition caller v2: typed local execution yields

## Problem

The first passing compiled-interface live pair exposed an accounting defect at
the composition boundary.  The bounded runtime returned `SAFE_YIELD` with
reason `unknown_state` after one completed action, but caller v1 converted every
non-successful execute result to the generic reason `failed`.  The GUI remained
safe, yet the outer result no longer told a planner whether an action had
already happened or why local continuation stopped.

## Contract

`adaptive_acquisition_caller_v2.py` leaves the v1 acquisition, comparison and
model-call accounting paths intact.  Its execute adapter additionally accepts:

```json
{
  "status": "safe_yield",
  "reason": "unknown_state",
  "completed_actions": 1
}
```

The reason must belong to the bounded compiled-runtime yield vocabulary and the
action count must be a nonnegative integer.  The outer result remains
`EXECUTION_INCOMPLETE`, copies the typed reason, records the complete execution
progress object and reports `confirmed_partial` when at least one action
completed.  A yield before any action reports `not_attempted` and
`input_authority: none`.  Unknown reasons and malformed shapes fail closed.

## Evidence

The offline probe covers 18 retained-record and test-double scenarios on
Windows and WSL.  It includes partial and zero-action yields, legacy completed,
failed and delivery-uncertain results, malformed reasons, cold acquisition,
expansion, warm reuse, repair and incomplete usage.  The partial-yield model
accounting is byte-equal to the corresponding legacy execution scenario; the
new contract adds no model call.

The fresh live integration is reported in
[compiled GUI interface live v5](COMPILED_GUI_INTERFACE_LIVE_V5.md).  It
preserves `unknown_state`, one completed action and `confirmed_partial` across
the real GUI composition boundary.

## Limits

The offline block establishes branch and accounting mechanics.  The one live
pair establishes one integration instance.  Neither establishes a natural
yield rate, recovery success, token saving, latency improvement or broad GUI
coverage.
