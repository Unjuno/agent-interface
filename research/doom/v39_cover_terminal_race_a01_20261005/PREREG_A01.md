# V39 completed-terminal race probe A01

Frozen before the probe on 2026-10-05 (Asia/Tokyo).

**H.** On `origin/main` at `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`, `cancel_invalidated_cover()` accepts only a `cancelled` executor terminal. If its terminal wait returns `completed` with a verified empty release after planner interruption and cover-cancel request, the controller raises instead of treating the cover as already stopped. This can turn a safe cover-finished/invalidation race into controller failure while the planner turn is pending.

**T.** AST-extract the exact helper from the frozen source blob and call it with: (a) cancelled + verified-empty, (b) completed + verified-empty, (c) completed + nonempty, and (d) failed + verified-empty terminals. Preserve planner interrupt, cancel write/flush and terminal selection outputs. Separately evaluate a candidate condition that permits `completed` only when release is verified empty. No game, model, GUI, OS input, or runtime is invoked.

**D.** Reproduction if (a) returns and (b) raises solely on status despite an empty verified release. Candidate is acceptable for further review only if it accepts (a)/(b) and rejects (c)/(d). This probes a controller contract, not frequency or live impact.

**C.** The strict `cancelled` requirement may be intentional to distinguish an explicit stop from natural completion. However, a matched completed terminal with verified empty keys/buttons already establishes that no action authority remains; planner interruption is sent independently before waiting.

**U.** Synthetic terminal rows do not establish race occurrence, runtime scheduling, external input neutrality, planner behavior, or a gameplay effect. The current #59 live threat-exposure allocation remains unassigned and is not replaced by this construction probe.

Source: `research/doom/map01_overlap_controller_v39.py` from frozen Git tree `origin/main` (`018934cdf45fcabffcc4efe25b5c7b3d59bd459f`). No source modification or live allocation is part of this probe.
