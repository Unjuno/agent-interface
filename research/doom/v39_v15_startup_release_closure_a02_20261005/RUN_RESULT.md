# A02 run result

A02 called the actual current-main `session_map01_v15.main()`. V15 selected `doom_owner_thread_release_batch_backend_v1.Backend` and `executor_v13.Executor`; the declared V12-main shim then drove the selected backend through two FakeXlib DOWNs and reverse UPs. The trace shows no keymap query between the two explicit UP injections, two owner-bound receipts, two completed release rows, and an empty post-batch/final synthetic state.

The frozen auditor returned **FAIL** on `v15_recorded_exact_source_manifest`: the freeze binds two import dependencies (`executor_v3` and `executor_v11`) that V15's own merged `sources.json` does not include. The separately labeled post-hoc audit reads only the captured runner output, verifies those two source hashes independently, and confirms all paths V15 actually declares against the frozen manifest. It does not rerun the candidate or replace the frozen FAIL. Overall disposition remains `FAIL_FROZEN_AUDITOR_MANIFEST_CHECK`.

WSLc warned that swap/cgroup accounting is unavailable; no memory-limit enforcement claim is made. Scope is synthetic startup/backend composition only. This does not execute the V12 session/controller, actual X11, game, GUI, model, OS input, V39 threat response, feedback, recovery or task outcome.
