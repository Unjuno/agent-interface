# Result: actual stdio transports cancellation and early fake cleanup

Source baseline main `155dc4f69c0c5aeda36788d652823ca2efc5d8fb` (#8941).
Normal and optimized Python each completed the frozen six cells, using a fresh
child process per cell. Real MCP client/session/stdio and standard server main
performed discovery, source observation, minting, guarded input, results lookup,
cancellation and close. A bootstrap installs Fake X and a trusted additional
visual guard; no MCP tool or owner implementation is replaced. This guard is
local operator configuration, not a remotely supplied callback or default tool.

| Arm / condition | Before capture gate is released | Final result |
|---|---|---|
| Both healthy | No artificial gate | CTRL+a exercised; completed, verified fake-neutral cleanup |
| Target-query-only / cancel | Cancel acknowledged without release confirmation; result pending, CTRL held | Failure and verified fake cleanup after gate release; no a press |
| Target-query-only / original expiry | Result pending, CTRL held | Same refusal/cleanup after gate release |
| Active visual isolation / cancel | Failed input result received by real stdio client; CTRL released, gate still closed | Retained result matches; no a press |
| Active visual isolation / original expiry | Same result-before-gate-release ordering | Retained result matches; no a press |

All cells close explicitly. Retained lookup emits no new input and matches the
original bridge result. Isolated readers close on their own thread after the
gate resumes; the parent waits for this marker before ending the stdio context.
Both saved-data audits pass **108 checks and reject five mutations**, and each
pins **188 output artifacts**. Freeze pins **177 source files** and dependency
versions. All first normal/optimized collections completed successfully; no
retry, real GUI input, WSL/container or model allocation was consumed.

This adds actual cross-process cancellation/result-transport evidence to the
direct API composition. It does not establish live X behavior or physical input
release. Platform/preflight/focus and query responses are fake. The bitmap and
emission files are harness observations, not an independent physical observer.
Parent perf-counter timestamps bracket client receipt only; fake child deadlines
are a separate clock. The three-second parent watchdog and ten-second gate guard
are harness caps, not a release guarantee, confidence bound or efficiency result.
No application/model task success or provider receipt is claimed.

Adoption decision: retain the explicit #8941 mode and its scoped transport claim.
The generic fixed-delay wait and input send/sync/readback/close remain separate
synchronous boundaries. #17 remains open. Next qualify bounded unknown/recovery
reporting around input transport faults while preserving one input writer, then
independent application effect and live matched efficiency when permitted.

`normal/` and `optimized/` retain complete bridge directories, child stderr,
input/gate/close markers, client metadata and parent receipt brackets. The
collector refuses existing output directories or changed frozen source. To
recheck saved data without launching a server:

```powershell
python -B -m research.live_control.guarded_stdio_cancel_20261015.audit research/live_control/guarded_stdio_cancel_20261015/normal --output <fresh-audit.json>
```
