C07 — ExecutorV12 release-publication ordering counterexample
Date: 2026-10-04

Frozen source: ExecutorV12 as present on the PR #7449 stacked candidate at the time of the test. The gated test blocks cancellation-release publication after the owner release exists. The worker emits terminal before the gate is opened; test result is FAIL (exit 1). This is a deterministic counterexample to terminal-before-publication ordering in that v12 path.

This is an in-process fake-backend regression only. No game, X server, live input allocation, or live MAP01 run was used. The result does not characterize task-effect, performance, recovery, or resource bounds. See FROZEN files, raw.txt, and exit.txt.
