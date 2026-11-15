# Attempt ledger

1. **Default 5 s startup:** MCP initialize/tool listing and public G10 prepare
   succeeded. Launch returned UNKNOWN / `CALC_LAUNCH_OR_DISCOVERY_FAILED` with
   `owned guarded process startup timed out`. Custody UNKNOWN, authority false,
   and input not dispatched. No target launch occurred. The runner removed its
   temporary directory, so only the structured fields in this note remain.
2. **No owned-process flag:** Calc launch construction was refused because the
   registered launch factory requires guarded-owned X11. No task input ran.
3. **Test-only 20 s wait:** The first launch response was pending at 10 s. Exact
   `interface_results(call_id)` polling reached `candidate_found`. Parent effect
   verification was UNKNOWN because the fake target-exit receipt had an invalid
   package version.
4. **Correct target-exit receipt:** Parent effect verification returned
   `verified/true`; an unrelated assertion then looked for a synthetic pixel
   marker the stub graph never writes. The actual G10 fixture retains saved
   FODS files, so the assertion was corrected to check those exact paths.
5. **Final normal and optimized attempts:** Both passed 1/1. The test-only
   20 s startup override remains explicit; production startup duration was not
   declared passing.
