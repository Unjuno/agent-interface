# A02 — STOP_MAIN_ADVANCED_BEFORE_CANDIDATE

A02 froze construction against `cd3a410a930e5f1e29a22cee36d9a149fbc106c7`.
Immediately before any formal candidate invocation, `origin/main` was
re-fetched and observed at `f44c5f5724ed2ba1d44cab9a8b3f88f5179c014c`, while
the branch merge-base remained the frozen `cd3a410a...` commit. This violates
the exact-main execution gate.

Disposition: STOP. Candidate invocations 0; auditor invocations 0; retries 0.
No candidate or auditor container was started and no scientific output exists.
The original A02 `FROZEN.json` and sources are retained unchanged. A03 is a
separate allocation under `successor_a03_seed20261011/` with a new base and
fresh seed; it is not an A02 relaunch.
