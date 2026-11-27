# R43 — current-main post-recovery native task cohort

## Question

Can the public Win32 caller, after an expired source action is independently recovered, complete a distinct follow-up fixture task with the task effect independently verified? This repeats the narrowly scoped R41/R42 path on the current main runtime and adds five frozen attempts.

## Frozen design

- Baseline commit: `612b857d7c1c6a951d3f055862a5141dbc9c7637`; runtime tree OID is recorded in `conditions.json`. A source audit found no `runtime/` changes from R42's `dc1f119bcb4094d0b58e70ffa273596f206c6c7a` to this baseline.
- Five sequential attempts, once each, in frozen order. Any failed condition stops the cohort; no retry or replacement.
- Per attempt: create a dedicated source fixture; exact-window Computer Use activation; dispatch one `A` chord with 2 s authority; preserve source status UNKNOWN/release-unconfirmed/task success null/replay denied; observe the delayed `a` effect without attributing it to that source action; verify producer absence; issue at most one public orphan recovery; require release, neutral readback and complete 2 s horizon; create a separate fresh process/window and dispatch one `B`; independently verify a `b` event within the exact public dispatch interval and close both fixtures only after success.
- Window placements are frozen at source `[1400,600]` and follow-up `[950,600]`. R42's runner did not use the positions written in its conditions. R43 binds launch coordinates to the frozen values, records `GetWindowRect`, and stops on any mismatch before dispatch to that target.
- Computer Use may activate the exact returned window and inspect it, but sends no pointer or key input. This prevents UI setup from contaminating the fixture event stream or task state; public MCP dispatch remains the only task input path.
- Use no model/provider. Each attempt starts only if the persistent Win32 custody fence is clear; no Docker, WSLc, downloads, or installs.

## Pass rule and scope

Scoped cohort pass requires all five attempts to satisfy every source, recovery, follow-up effect, release, cleanup and fence assertion. One STOP or failure is retained and fails the frozen cohort; do not complete later attempts. Even 5/5 is a controlled single-host fixture result, not a population reliability estimate, arbitrary-app/MAP01/Calc result, provider efficiency comparison, Research Preview acceptance or distribution qualification.

## Independent review

`audit.py` will verify freeze and source hashes, frozen denominator/order, per-trial identity and position receipts, source UNKNOWN/no-replay, recovery receipt linkage and horizon, follow-up task-oracle identity, the event timestamp against the public execution interval, cleanup/fence state, and the final packet manifest. Raw attempt files and process exits remain in `raw/`.
