# V39 release sink failure T0

This construction test asks whether the exact release-publication helper at PR #7474 head `3e498aebd77e500d5a7b1ac9d434d37350a9f597` preserves delivery custody when the configured event sink fails. The nearby #7429 branch already has a related attempted-versus-confirmed publication repair and release-sink regression; this experiment targets the distinct #7474 executor blob and tests whether that repair is present there.

`executor_v13.py` is pinned to Git blob `7f308a0dd863af534f764f657d603b4921ba1c6a`. `run.py` AST-loads the exact `_release_event` and `_publish_cause_once` methods, then tests a successful sink, a sink that raises before acceptance, and a sink that accepts then raises. `audit.py` independently checks the raw outcomes and the exact `_run` caller structure.

The successful control publishes one `input_released` event. In both failure cases the helper raises after adding the action ID to `published_release_ids`; its next call is suppressed. The before-accept case therefore loses the event, while the accept-then-raise case has ambiguous delivery. Neither case records a `delivery_unknown` event. `_run` calls this helper at top level in its `finally` block before `release_all` and terminal publication, so the escaped sink exception also bypasses those subsequent operations in this source path.

This is a host-Python synthetic construction test against exact source methods. It is not a full executor-thread schedule, does not exercise a live owner, real sink, game, model, or input, and does not establish physical release behavior. WSLc was not used because the shared WSLc CLI inventory call remained unresponsive while many other WSLc processes were present; no container was launched.

The run was exploratory and not prospectively frozen; it is retained as construction evidence only. The tested source head was rechecked after the run and remained unchanged.

Run from the repository root:

```powershell
python research/doom/v39_release_sink_failure_59_7474_t0_20261004/run.py
python research/doom/v39_release_sink_failure_59_7474_t0_20261004/audit.py
```
