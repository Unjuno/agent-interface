# Standard-caller release-order composition — 2026-10-19

## Question and result

Can the public MCP caller confirm input release after it retires a blocked owner,
observes that exact X client disappear, and receives an empty keymap readback from
a fresh cleanup connection, when the old owner's key-down is still queued and
arrives afterward?

**Result: the caller correctly remains fail-closed; the release claim is not
proved.** The composed Fake X sequence applied the old queued `KeyPress` after the
fresh cleanup receipt reported verified empty keys/buttons. Both the immediate
cancel response and terminal result retained `release_confirmed=false`,
`cleanup_status=UNKNOWN`, `task_success=null`, and `replay_allowed=false`; the
cancel response retained `late_server_request_possible=true`. The modeled keymap
was down after the delayed old request was applied.

This is a software-policy counterexample and regression, not a live X-server
result. The test injects the disconnect and successful fresh-client release
receipts; it establishes that the standard caller does not promote those receipts
to overall release confirmation when ordering remains unproved. It does not show
that XRes or a real cleanup worker provides those receipts, nor prove a physical
release deadline or application effect.

## Frozen construction and conditions

- Fixed source: the `runtime/cli_v1/test_mcp_owned_process.py` test
  `OwnedProcessMCPTests.test_standard_cancel_keeps_unknown_after_release_readback_then_late_down`.
- Base commit: `d6f0fb8f70eba87728b777d2b83eb74709ae8cea`; test source SHA-256:
  `7d89c9bb69145b1dfd2071fd52a48643dab354929e58cf55592c6dad5dd57243`.
- The spawned standard MCP owner uses the existing per-connection Fake X queue.
  It accepts a `KeyPress` for keycode 1 (`CTRL`), then blocks in the owner's
  `sync()` before that request is applied to the modeled keymap.
- The cancel path is exercised through `interface_guarded_cancel`. The test
  injects an exact-owner retirement and XRes `disconnected` receipt, then a
  cleanup `readback_verified` receipt with an empty key/button set.
- After cancellation, the harness applies the old owner's queued `KeyPress`.
  This deliberately tests a cross-client ordering counterexample; it is not a
  claim that a live X server necessarily schedules this order.
- The same source's four neighboring regressions cover unknown/present-client
  fail-closed behavior, target process-generation alias refusal, blocked-owner
  cancellation, and the lower-level queued-down counterexample.
- No WSLc, Xvfb, Docker, real desktop, live application, formal allocation, or
  new task-effect oracle was used. The successful cleanup receipt is mocked to
  test caller composition only.

## Verification

Five selected `OwnedProcessMCPTests` passed in normal and optimized Python. Logs
are preserved under [`raw/`](raw/):

- `normal.log` — SHA-256 `ED19163F7EA588A973DCF0FC46D2B4C8B6316EB551EBE1847370195D7D20EF23`
- `optimized.log` — SHA-256 `9F69782465B7186BC9ADBDEEB4C0F0798DE6D121866DC02550A68E57204839A9`

The local test environment used `uv 0.9.26`, CPython 3.14.2, `mcp 1.30.0`,
`python-xlib 0.33`, and `Pillow 13.0.0`; the temporary environment constrained
`mcp<2` because the repository imports the v1 `FastMCP` API. No dependency file
or environment configuration in the repository was changed.

## Next discriminator

The remaining release question is an independently justified server-side fence
that orders or drains all accepted requests from the retired owner before a
separate release can be treated as final. XRes client disappearance alone does
not establish that property. Test that boundary on an eligible real X server only
under a currently verified unused allocation; otherwise retain UNKNOWN. Then
qualify the standard caller against an independent application-effect reader,
bounded recovery, and matched control tasks. This result does not close Issue #17.
