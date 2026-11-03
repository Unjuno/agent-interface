# Calc plan evidence join — integrated boundary result (2026-11-04)

## Result

Pinned Docker image `agent-interface-xvfb-mcp:late-input-r19`, offline, 2 CPUs, 4 GiB memory/4 GiB total memory+swap, 256 PIDs, source read-only and a separate evidence mount. Final runner exited 0 (`docker-exit-final-08.txt`). The evidence-join plus reuse-horizon unit set passed 27/27 in normal mode and 27/27 under `-O`; the composed Fake App Server Calc test passed 1/1 in 9.450 s. Logs are `normal.log`, `optimized.log`, and `composition.log`. `raw-runtime-final-08/` retains provider-call, provider-ledger, App Server protocol and Fake X evidence. `SHA256SUMS.txt` hashes all packet files except itself.

The run separates observations that must not be joined as one successful provider task:

- Provider accounting retained seven model attempts, four successful Fake Planner generations and 32 public MCP calls. Total usage is incomplete because timeout and cancellation attempts have unavailable usage. The Fake Planner echoes fixture arguments; it is not a model-authored plan or provider efficiency measurement.
- The provider-routed compiled call with attempt `calc-offline-e2e-01` is rejected as `invalid_request` / `CALC_BINDING_NOT_MINTED_FOR_REVIEWED_SOURCE`; it dispatches no operation or input, leaves task success unknown and replay disabled. The deliberately mismatched attempt is rejected as `CALC_REVIEW_SOURCE_STALE`.
- A separate nested direct Fake X Calc path produces a saved FODS whose parsed values match A1=24680 and A2=13579. Its artifact verifier reports task effect true and owner close confirms release. These receipts have a different execution path/call and cannot prove success for the rejected provider-routed request.
- The strict evidence join rejects unknown final task success, duplicate attempt/artifact/owner custody, digest substitutions, invalid repair sources and missing independent score.

This run pinpoints an offline integration seam: the provider-routed compiled request lacks the mint receipt for the reviewed source in that MCP session. It does not demonstrate live Calc GUI behavior, a successful model-authored cold/warm/repair horizon, efficiency, WSLc, MAP01 or long-duration Docker Desktop stability. Earlier failed packet attempts (`raw-runtime`, `raw-runtime-rerun-02`, and `raw-runtime-final-03` through `-07`) remain for audit; only final-08 is the successful current source run.
