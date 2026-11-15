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

6. **Post-merge main rerun (2026-11-16):** On merge commit
   `156fd8fad2c94e8ece74e2f6ae4885f9cd998636`, normal and `-O` both passed
   1/1 (15.107 s / 15.359 s); owner startup measured 10.890 s / 11.578 s.
   Complete raw logs are `raw/rerun-normal.log` and
   `raw/rerun-optimized.log`. This repeats only the Fake X/archived-FODS
   receipt-shape check, and the production 5 s startup boundary still fails
   in this Windows nested-spawn fixture.
