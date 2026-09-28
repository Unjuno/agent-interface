# Issue #5156 owner-side automatic release call graph

## Result

`PASS_AUTOMATIC_RELEASE_OUTSIDE_CALLER_BRACKET` at pinned source/control-flow scope.

The exact InputOwner v10 source contains four local `release()` call sites. Three can run autonomously in the owner thread: stop requested, deadline/cancel/focus/surface invalidation, and thread-exit cleanup. The remaining site handles a queued `release` or `close` operation. The v3 wrapper's timed `_inner.call(operation, lease, key)` is only on a caller's synchronous path. It cannot enclose later autonomous cleanup after that caller has already returned. Therefore the registered universal nesting rule cannot hold for every automatic-cleanup case.

## Frozen inputs

Pinned commit: `16421aefa2ec357b79e3fd3dc307b32955bc6fab`

| File | SHA-256 of fetched UTF-8 bytes |
|---|---|
| `research/live_control/input_owner_v10.py` | `ec4d6969d4c0cae2ee0a2989455a2fe87f930d90aeb3451afd3450c7c85e9718` |
| `research/live_control/input_transition_owner_v3.py` | `5ffdbb3679451fefdc3836917d43d924f0f43c8082d21327207ecefbd87f5be6` |

The standalone stdlib analyzer checks these hashes before parsing. It found owner release calls at lines 205, 219, 261, and 356, and two wrapper delegations of `_inner.call`. The assertions require exactly four classified owner calls, exactly two wrapper delegations, and exactly three autonomous cleanup calls.

## Reproduction

With the two frozen source files available locally:

```text
python research/analysis/issue5156_owner_autorelease_callgraph_v1/analyze_callgraph.py --owner-source research/live_control/input_owner_v10.py --wrapper-source research/live_control/input_transition_owner_v3.py
```

The analysis was independently executed on the Windows host with Python 3.11 against files fetched from the pinned GitHub commit. No X11, Docker, model/provider, GPU/CUDA, GUI, or OS input operation occurred. The analyzer is preserved as the rerunnable source artifact.

## Limits and next gate

This proves a source-level control-flow fact only. It does not measure XTest or XSync timestamps, physical key-up, application consumption, or useful task effect. It is not the formal X11 allocation and does not authorize one.

Before any fixture run, correct the measurement scope so explicit caller-requested key-up and autonomous cleanup have separate receipt/ordering rules. Then freeze a new construction/audit package and obtain an exact shared-container lease. Preserve the existing #5156 hypothesis and this result; do not run the formal allocation under its universal caller-nesting rule.
