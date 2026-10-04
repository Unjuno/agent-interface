# MAP01 v15 cleanup successor

The Codex review of PR #7440 head `b90cf06` found that a failing final scorer
sample in `_GameProxy.close()` skipped the wrapped game's `close()` and left the
proxy marked open. The frozen v14 source and C02 evidence are deliberately
unchanged: that evidence records the exact v14 source chain and must remain
reproducible.

`session_map01_v15.py` is a separate, unrun successor. It attempts the final
sample, always attempts the wrapped close, and always finalizes proxy state. A
sampling error remains the primary surfaced error; if close also fails, that
close error is retained as its cause. `test_session_map01_v15_cleanup.py`
exercises those error paths with a fake game only.

This is source-level cleanup evidence only. No MAP01 runner, game, X server,
model, physical input, or formal/live allocation was executed or authorized.
