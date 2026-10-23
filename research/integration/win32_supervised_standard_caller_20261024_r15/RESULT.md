# R15 launch result

**Outcome: PRELAUNCH_FAIL_OR_UNKNOWN; no live trial occurred.** The frozen
probe refused to start because `docs/CURRENT_GOAL.md` had an uncommitted tracked
change. Its source preflight ran before output-directory and fixture creation,
hook installation, public MCP calls, or native input. The process returned exit
code 1 with `RuntimeError: source commit mismatch or tracked source is dirty`.

No trial data was generated, and the hook-timeout hypothesis remains unanswered.
Preserve this refusal and do not rerun R15. A separate attempt must use a clean,
committed source tree and a new attempt ID/sentinel. See `launch_failure.json`;
`SHA256SUMS.freeze` preserves the intended R15 inputs.
