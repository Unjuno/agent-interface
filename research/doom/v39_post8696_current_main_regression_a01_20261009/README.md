# V39 and release-terminal regression after PR #8696 (A01)

This run covers current `main` at `4fb44827372c1fe4872a1add532c12544a5a9f81`, which includes PR #8696's terminal pending-UP custody ordering fix. The 81-test V39/controller, dual-signal, terminal-release, pending-observation-drain, and V15 session suite was combined with the 18-test ExecutorV13 suite: 99/99 passed normally and 99/99 under `python -O`.

The test modules and relevant executor/controller sources in the executed checkout were byte-for-byte identical to the recorded current-main commit; the checkout commit also contains the prior post-#8691 regression evidence package from this branch. Exact commands, raw output, and hashes are retained here.

Scope remains model-free source regression only. No game, GUI, OS input, app-server, or model was started. This does not establish live threat response, physical key state, independently useful feedback, bounded recovery, or MAP01 outcome. The live A07 allocation was not touched.
