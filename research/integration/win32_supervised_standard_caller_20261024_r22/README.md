# Standard Win32 caller short-block recovery — R22

R22 is one new public stdio-MCP trial on the user-authorized Windows PC. It
uses a fresh owned fixture and generation, one dispatch, one cancellation, and
one injected Q-down held inside the probe's low-level callback for 250 ms after
the public cancel response. On callback return, the original event is forwarded
normally. The probe records exact producer identity/retirement, public action
and cancellation receipts, independent same-generation key-state readback, the
fixture's saved sentinel, and bounded cleanup.

The independent readback taken before callback return is explicitly
non-discriminating. Product recovery passes only if the public caller reports
`recovered` with `release_confirmed=true`, the exact producer retires, and an
independent readback taken after callback return observes Q-up on the same
generation before any emergency cleanup. Any emergency Q-up is labeled
cleanup-only and makes the product recovery outcome FAIL_OR_UNKNOWN. Runtime
`task_success` remains null; the fixture effect precedes the cancellation
point, so this trial does not claim a task effect after recovery.

The conditions and code hashes must be frozen before running `probe.py`.
`preflight.py` compiles the runner and installs/removes the owned hook without
native input. Run the probe once only. Preserve all outcomes; no retry, WSLc,
Docker, registry change, replay, or fallback input is allowed by this packet.
