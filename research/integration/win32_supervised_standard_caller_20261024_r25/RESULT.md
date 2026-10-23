# R25 result — unsupported 12-second response wait

R25 is preserved as `FAIL_OR_UNKNOWN`. Its input-free preflight passed, and it
started a new fixture and supervised public session with a distinct target
generation. The one dispatch request used `wait_for_result_ms=12000`, which the
public caller rejected immediately as `INVALID_RESPONSE_WAIT` with
`operation_invoked=false` and `replay_allowed=false`. The event journal contains
only fixture readiness; no effect file exists. The fixture exited cleanly and
the previous foreground window was restored. No input was sent, and there was
no retry.

The current caller source accepts response waits only from 0 through 10,000 ms
(`runtime/cli_v1/mcp_server.py`, the `submit` validation at the frozen source
commit). R24's persisted operation completed and released at about 8.824 s,
within that upper limit. R25 therefore identifies a protocol constraint rather
than an operation failure. R26 uses a fresh fixture/session/generation and the
supported 10,000 ms maximum; its probe records the actual release timestamp
separately from the public response time.

The session close returned `closed` with `release_confirmed=false`; as no input
was invoked and the event journal remained empty, this is preserved as no
input-side effect rather than counted as a release success. Runtime
`task_success` remains null. This result establishes no task effect or release
behavior.
