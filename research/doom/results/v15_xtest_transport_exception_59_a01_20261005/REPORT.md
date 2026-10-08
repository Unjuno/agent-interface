# V15 XTest transport-exception construction A01 — 2026-10-05

This exploratory synthetic construction probes a specific untested path in PR #7974 at head `b5fbfed1c896f587dd5dfeb30c2735d63f670264`. It uses the exact PR-head `input_owner_v12.py` source bytes, with `executor_v3.py` and `lease.py` retained for imports.

H: if the first XTest KeyRelease send or its sync raises during `up_batch`, later ordered UPs and per-key receipts are skipped before a separate terminal cleanup call.

T: hold W and A in a fake X display; inject one failure at the first release send or first sync; capture the thrown result, release trace, receipt count before cleanup, and subsequent cleanup result.

D: reproduced only if each case raises during `up_batch`, records one initial KeyRelease event, and has zero explicit-keyup receipts before cleanup. Cleanup success is a separate observation and does not erase the release-batch failure.

C: a setup-time injected error could masquerade as a batch failure; the preserved first construction attempt did exactly that. The corrected runner arms the fault only after both key-down calls return.

U: this is native Windows CPython 3.12.10 with a deterministic fake X transport. It does not test V15/V13 terminal composition, button release, a real X server, GUI/game input, physical state, application effects, or WSLc. It is not live allocation evidence or a WSLc result.

The finding supports the focused review request on [PR #7974](https://github.com/Unjuno/agent-interface/pull/7974#issuecomment-5988713534); it does not establish a runtime failure rate or task-level impact. `audit.py` independently checks raw outcomes and frozen source hashes.

Reproduce from this directory with `python runner.py > RAW.json`, then `python audit.py`. The exact source snapshot is under `frozen_source/`.
