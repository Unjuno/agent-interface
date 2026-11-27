# R05 result: unforced callback drain diagnostic

Disposition: **DIAGNOSTIC_INCONCLUSIVE_FOR_TIMEOUT_CLEANUP**. All six instrumented public Fake caller tests passed (3/3 normal, 3/3 `-O`), each logging `Ran 1 test ... OK`. The exact child exit codes (all 0) were returned by the fixed PowerShell runner and are retained in the per-attempt `.exit` files; `exit-source.txt` preserves the execution summary that supplied them. No attempt was retried.

The test now records every `run_coroutine_threadsafe` Future, includes callback exceptions and Future-done state in assertion diagnostics, and drains outstanding API Futures for at most 30 seconds before `interface_close` and temporary-directory teardown. `git diff --check` passed before running. All six outcomes passed the existing caller's semantic assertions, which require exact effect identity, verified recovery release/horizon, source UNKNOWN/null, replay denied, and one oracle success.

However, none of the six attempts hit the original 8-second callback timeout: all Futures were already done at the semantic assertion, and the 30-second drain branch was not exercised. There was no `.report.json.tmp` cleanup collision. Therefore these results show the instrumentation does not disturb the ordinary successful path, but they do **not** establish that draining prevents the R04 timeout teardown collision or explain the two uncertain action failures. A new deterministic delayed-callback diagnostic is required.

This is still Fake/local test-harness evidence only. It is not a reliability estimate and does not cover native input, live GUI/MAP01, efficiency, WSLc, preview graduation, or distributable-runtime acceptance.

## Evidence custody

The preregistered design and frozen source hashes are in `PLAN.md` and `conditions.json`. Six numbered raw logs and exit-code files plus a preflight write probe and exit-source summary are under `raw/`. `SHA256SUMS.txt` covers the packet other than itself.
