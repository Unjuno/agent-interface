# R17 result

R17 used one public stdio-MCP dispatch and cancel on the user-authorized local
Windows PC. Cancel returned in 1.580 ms. The callback hold lasted 2049.2 ms;
same-call polls remained `running` / `pending` with release unconfirmed, and
the exact producer exited 2051.2 ms after cancel. The R17 sentinel effect was
independently observed and cleanup succeeded, but no recovered release receipt
or independent UP proof arrived while the callback was held. The frozen audit
is `FAIL_OR_UNKNOWN` (19/20). Preserve as a blocked-release result; no rerun.
