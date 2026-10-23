# R03 result: FAIL_OR_UNKNOWN before dispatch

The frozen audit scored 7/15. The one public `interface_dispatch` request was
rejected immediately as `INVALID_RESPONSE_WAIT` because its configured
`wait_for_result_ms=30000` exceeded the standard caller's accepted range of
0..10000 ms. The raw response records `is_error=true`,
`operation_invoked=false`, and no call ID. No result readback was attempted,
the fixture journal contains only `ready`, and no effect file exists. The
public close response reports a closed supervised session with zero calls; the
fixture exited cleanly and the prior foreground window was restored.

This is a frozen parameter-preflight failure, not a runtime execution result.
The packet is not rerun. R04 uses the maximum accepted 10000 ms wait and checks
`input_dispatched=true` in the same call's terminal retained report, including
when the initial public response is `pending`.
