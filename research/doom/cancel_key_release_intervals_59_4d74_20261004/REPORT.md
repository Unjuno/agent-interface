# Cancellation batch per-key release interval composition

This construction check closes a source/telemetry gap found during the current-main #59 integration audit. The selected release owner now records one conservative interval for each key it releases while cleaning up a cancelled lease, and the V13 no-authority `input_released` event retains the exact owner record.

**H — Hypothesis.** For each held key released by cancellation cleanup, `owner_release.key_release_intervals_ns` contains exactly one row with the matching keycode and integer bounds from that key’s XTest release request start through the completion of the shared XSync. The bound ends no later than owner key-state verification. `ExecutorV13` publishes the same owner record inside `input_released`, with no input authority grant.

**T — Test.** A fake-Xlib owner-thread test admitted two keys, set cancellation, and checked both request intervals, key identities, order, verified-empty state, and propagation into `input_released`. The exact pre-repair source was first tested after staging the missing `lease.py` dependency.

**D — Result.** The pre-repair baseline failed because `key_release_intervals_ns` was absent. The repaired candidate passed the new owner/publication regression and 15 adjacent explicit-up, transition-receipt, V13 watcher, and release-batch tests (16 total). `py_compile` and `git diff --check` also passed. The initial incomplete baseline staging attempt is retained separately as STOP; it lacked `lease.py` and made no claim about the source defect.

**C — Competing interpretation.** A single XSync completion timestamp conservatively bounds each request; it does not identify the physical key-up instant or when an application consumed it. Independent key-state verification remains a distinct assertion.

**U — Uncertainty and limits.** This is fake-Xlib/source-composition evidence only. It does not test a real X server, OS input, physical key transition, GUI/game effect, model, useful feedback, full session, or bounded recovery. The candidate suite ran on the macOS host because the configured OrbStack Docker daemon returned an unsupported content-store operation during image listing. No game/GPU allocation was used. The private #59 game lane remains unassigned.

The exact freeze, commands, source hashes, raw output, and an audit script are in this directory. Historical STOP and FAIL outputs are preserved and not relabeled as candidate results.
