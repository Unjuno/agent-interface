# Query-private evidence-location lookup — #8000

- **Status:** Unverified transfer proposal; eligibility is on hold.
- **Source:** [Issue #8000](https://github.com/Unjuno/agent-interface/issues/8000), successor to [#6125](https://github.com/Unjuno/agent-interface/issues/6125); retained eligibility evidence [PR #8212](https://github.com/Unjuno/agent-interface/pull/8212).
- **Idea:** If workers genuinely retrieve evidence locations through a shared directory, test whether the directory operator can be prevented from learning which record index was requested. Compare maintained single-server computational PIR only with direct and equal-shape padded lookup; keep evidence integrity, freshness, scope, authorization, and semantic truth as independent gates.
- **Outcome:** T0 returned `HOLD_NO_ELIGIBLE_LOOKUP`: the recorded scan of 14,169 tracked research files found no qualifying cross-worker retrieval trace with sensitive query identity and observable discovery/reacquisition cost. Separately, the attempted WSL container smoke stopped with `STOP_WSL_CONTAINER_CLI_HANG`; container readiness was not verified. No PIR fixture, candidate, or container workload ran. These are distinct workload and environment dispositions, not a privacy result.

## Resume condition and limits

Resume the workload question only when a retained trace establishes the stated lookup eligibility elements. Do not fabricate demand from a synthetic directory, and do not treat the container STOP as permission to fall back to another execution boundary. Even a future method pass would cover only the declared server view and protocol assumptions; it would not hide client/network identity, later holder retrieval, timing/size/frequency unless explicitly modeled, or prove the located evidence true or authorized.
