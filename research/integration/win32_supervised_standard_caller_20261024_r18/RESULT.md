# R18 result

R18 added exact producer PID plus creation-time liveness sampling to one public
stdio-MCP trial on the user-authorized Windows PC. Cancel returned in 1.453 ms.
The callback stayed held for 2002.4 ms, while 32 same-call polls remained
`running` / `pending` with release unconfirmed. The first liveness sample, 3.1
ms after cancel, was indeterminate (`WAIT_TIMEOUT`); the next sample at 251.0
ms and subsequent samples through the hold saw the exact producer identity as
exited. After the callback returned, the producer-exit witness was 2004.2 ms
after cancel. This supports (but does not directly trace) the inference that
producer retirement can precede completion of blocked recovery. The exact R18
effect and local cleanup passed; the frozen audit is `FAIL_OR_UNKNOWN` (19/21)
because it expected the producer to remain alive. No release or recovery was
proved; no rerun.
