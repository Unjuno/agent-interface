# R16 result

R16 used one public stdio-MCP dispatch and cancel on the user-authorized local
Windows PC. The exact Q callback remained held for 1248.4 ms; cancel returned in
1.287 ms. The same-call polls stayed `running` / `pending`, release remained
unconfirmed, and the producer exited 1250.1 ms after cancel. The independently
read fixture effect was stale R14 text rather than the R16 sentinel, so task
effect did not pass. Fixture, hook thread, and foreground cleanup succeeded;
public close reported closed with release still unconfirmed. The frozen audit
is `FAIL_OR_UNKNOWN` (18/20). Preserve this as a failed effect check; no rerun.
