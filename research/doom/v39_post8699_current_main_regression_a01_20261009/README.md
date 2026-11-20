# V39 and ExecutorV13 regression on main 74fc81e (A01)

Executed the existing focused regression set on exact `main` commit `74fc81e0a447ad05e4a2220b16d7949979635fb9`, including the pending-observation test change merged by PR #8699. The set contains 100 tests across the V39 controller, dual-signal, terminal-release, pending-observation-drain, V15 session, and ExecutorV13 modules.

Both normal and optimized (`-O`) runs passed 100/100 using the Codex bundled Python 3.12.14 runtime. The system Python 3.14.5 attempt failed at import because Pillow is unavailable there; it ran 30 tests and is retained as environment diagnostic only, not the test result.

Scope is model-free source regression only. No game, GUI, OS input, app-server, or model was started. This does not establish live threat response, physical key state, independently useful feedback, bounded recovery, or MAP01 outcome. A07 was not touched.
