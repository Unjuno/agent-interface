# Public recovery task-verification negative controls R02

**Disposition: `PASS_LOCAL_ELIGIBILITY_MATRIX_AND_PUBLIC_COMPOSITION_ONLY`.** The frozen source is main `10680fe597678649c3de8a18a490462f4291edaf` (PR #10467). This candidate extracts the automatic-recovery task-verification gate into a pure predicate and makes its exact identity, release, and horizon rules independently testable.

## Result

Four focused tests pass in normal Python and under `-O` (4/4 each). The matrix confirms that an UNKNOWN action is eligible only when the automatic recovery receipt matches its operation and target generation, reports recovered phase/status, separately confirms release, and has `late_input_horizon_verified: true`. A mismatched operation, mismatched generation, non-recovered phase/status, missing/false horizon, disabled automatic-recovery marker, or unconfirmed release is rejected.

The public MCP integration positive control still joins observe, dispatch, exact-call results, recovery, and an independent task oracle. The source action remains UNKNOWN with null action task status; the caller returns `SAFE_YIELD / delivery_uncertain`, does not complete a graph transition, and denies replay. The public unknown-custody case still skips oracle invocation. The existing completed-action task-oracle path remains intact.

## Limits

Recovery, task effect, release, horizon, MCP server and oracle are fixtures. This is one local negative-control matrix and one positive composition per interpreter mode, not a reliability estimate. No live Win32/MAP01 effect, matched efficiency result, WSLc/Docker trial, Research Preview acceptance, or distributable-runtime acceptance follows. Issue #57 and the project-wide goal remain open.

## Inputs and raw evidence

`conditions.json` pins exact source hashes, commands, environment and acceptance rules. `raw/normal.log` and `raw/optimized.log` contain the exact successful test output and their `.exit` files record zero. `SHA256SUMS.txt` covers each packet file except itself.

## Next gate

Freeze multiple independent caller/recovery lifecycles with the matching and mismatching recovery receipts; preserve every attempt and verify no replay, delayed action, or held input escapes. Then move to a native task-effect/recovery trial under a fresh approved allocation. Keep #57 open.
