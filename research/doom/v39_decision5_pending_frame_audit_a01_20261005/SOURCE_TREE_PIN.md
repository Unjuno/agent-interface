# Source-tree pin for the decision-5 trace audit

The retained allocation consumed by `audit.py` is present in the historical source tree at commit [`53ec001a334e4077caf665ff56372cd4b0ccb068`](https://github.com/Unjuno/agent-interface/commit/53ec001a334e4077caf665ff56372cd4b0ccb068), under `research/doom/results/map01-v39-coast-liveness-live-01/`. The current `main` tree no longer carries that allocation directory; this rescue commit preserves the old commit in its ancestry and pins it here rather than copying or altering the original data.

For a future, separately authorized read-only replay, materialize that exact tree and pass its retained allocation directory to `audit.py`:

```sh
git worktree add --detach /tmp/unjuno-v39-decision5-source 53ec001a334e4077caf665ff56372cd4b0ccb068
python research/doom/v39_decision5_pending_frame_audit_a01_20261005/audit.py /tmp/unjuno-v39-decision5-source/research/doom/results/map01-v39-coast-liveness-live-01
```

The historical environment recorded for the original audit was CPython 3.11 with Pillow 10.4.0. This pin is provenance/documentation only: the retained audit result is not rerun here, and the interrupted decision-5 answer remains ineligible. The trace establishes exact image joins and event/protocol ordering only, not what an uninterrupted answer would have selected or any live-game outcome.
