# R10 result: 8/10 passes, Fake isolation not proven

Disposition: **MIXED (8/10), INVALID AS A PURE-FAKE COHORT UNTIL ISOLATION IS VERIFIED**. Normal passed 5/5; optimized passed 3/5. Each sample ran once, no retries or replacements.

The optimized failures both timed out during `interface_observe`; the caller Future remained incomplete at its 8-second timeout. In optimized-02, final close remained `busy` through the 30-second drain, and `TemporaryDirectory` teardown failed because the directory was still nonempty. The orphaned retained report was recovered read-only and copied to `raw/optimized-02-orphaned-report.json`. It says `observation_failed`, `Win32BackendError('invalid HWND for target fixture')`, `input_dispatched=false`, `side_effect_authority=false`, and owner `call_count=0`. Thus this failed attempt did not dispatch input, but it indicates the observed code path reached native Win32 observation rather than the expected fake callback. The source fixture is configured with HWND 123 and patches `runtime.cli_v1.mcp_server.observe`; why this sample reached the native backend is unresolved.

For passing samples the test's exact-effect/recovery/oracle assertions succeeded, but there is no retained per-sample observation receipt proving the fake observer was used. Therefore do not count the 8 passing samples as verified Fake-only effect evidence and do not compare their rate as a trusted cohort against R04/R09. R10 does show that the separate dispatch-report finalization race was not observed in the other eight samples, while the timeout/close-busy failure remains safety-relevant.

Next: isolate the supervised-win32 observation injection seam with a minimal normal/`-O` test and instrument callback identity before running any further lifecycle cohort. Keep the old R04/R09 results as historical records, but mark their Fake-only attribution unverified pending that audit.

Raw logs, exit codes, conditions, source digest, and the recovered orphan report are retained here. The report hash is in `SHA256SUMS.txt`.
