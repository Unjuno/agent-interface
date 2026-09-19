# Native finish-after lifecycle regression coverage

Additional automated coverage for PR #3154 while CI was queued. The actual
three-allocation evidence remains unchanged in `native-finish-after-01`.

Six new unittest cases invoke the current real harness main loop with inert
application/session/bridge dependencies, real temporary request/reply files,
the real immutable publication helper and real cleanup helper. They cover:
finish-after publication following cleanup; omitted/false flags preserving the
separate finish flow; false task evaluation retained; invalid/conflicting flags
before mint/input; refused input with no evaluation/replay; cleanup failure with
action, observation and successful task evaluation preserved independently.

The first construction run had two test errors because the fake second
observation omitted the `native.artifact.path` field required by the harness's
normal continuation prompt. That fake was corrected. Scoped module replacement
also avoids rolling back unrelated imports and reloading NumPy. No production
harness changes were made in this follow-up; it remains the live-tested source.

All 34 lifecycle/exchange/review/cleanup tests now pass. X11 CI includes this
test and the harness source. This verifies controller branches and publication
ordering, not GUI rendering, model quality or actual input delivery. The live
evidence supplies the separate application/input checks. Snapshots and hashes
are retained here; earlier experiment records are not edited.

```sh
PYTHONPATH=.:research/live_control python3 -m unittest \
  research/live_control/test_native_finish_after_v1.py \
  research/live_control/test_native_exchange_v1.py \
  research/live_control/test_agent_review.py \
  research/live_control/test_native_cleanup_v1.py
```
