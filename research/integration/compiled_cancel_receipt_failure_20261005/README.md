# Cancellation callback exception loses completed-prefix receipt

This additive #57 construction record independently reproduces the callback
exception path reported during review of [PR #7443](https://github.com/Unjuno/agent-interface/pull/7443).

## Result

Attempt 02 returns `PASS_REPRODUCED_COMPLETED_PREFIX_RECEIPT_GAP` from the
raw-only audit. On exact PR head
`6144a1b0a2c88f5d88ff1fce148381f1f22269e`, the synthetic client completes one
`enter` action and verifies empty input release. The cancellation callback
returns `False` for checks 1–3, then raises `RuntimeError` on check 4, when the
compiled loop returns after the completed action. The exception escapes the
adapter; no typed adapter receipt or `runtime_finished` event is returned. Only
one client command was issued, so no second action ran. The completed adapter
program and release remain in the client-side fixture, but the caller does not
receive the compiled receipt containing the completed prefix and pending
effect.

The pre-frozen attempt 01 is preserved separately as a setup failure: its fake
client omitted the temporary-output `root` attribute, so it stopped before any
client command. It is not pooled with attempt 02 and provides no evidence for
the callback behavior.

## Scope

This is a single synthetic adapter/core boundary probe using one retained
Chromium fixture image. It uses no live GUI, Mindustry/game process, Docker,
model/provider call, task input, or formal allocation. It establishes behavior
for this exact PR source revision, not callback failure frequency or product
impact. The PR's original adapter tests pass 10/10 but do not exercise a
throwing callback after an action terminal.

The integration requirement is to convert callback-source failure into a
fail-closed typed terminal that preserves completed transitions, release and
pending-effect evidence, while admitting no next action. A generic
`cancelled` label should not conceal callback infrastructure failure.

## Reproduction

From the repository root, with Python 3.12 and Pillow available:

```sh
python3 research/integration/compiled_cancel_receipt_failure_20261005/run_case_02.py
python3 research/integration/compiled_cancel_receipt_failure_20261005/audit_02.py
```

The archive under `sources/` is the exact PR #7443 adapter and complete
`runtime/core_v1` package at the pinned head. Attempt 02 was frozen in
`FREEZE_ATTEMPT_02.json` and committed as `3aed5278704747290ba7c2276ae8906298cb2896`
before execution. Raw result, stdout, stderr and audit are in `out/attempt-02/`.
Attempt 01's earlier freeze and failure are in `FREEZE.json` and
`out/attempt-01/`.
