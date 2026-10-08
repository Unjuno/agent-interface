# Formal allocation 05 — STOP

Immutable result of the single frozen invocation and its one independent audit for allocation `issue5236-formal05-20260930-01`. Do not rerun, replace, or tune this output.

- Frozen source commit: `83ec1a388ec3ea88a41a7f8c2ed0b3f0ec3cc54d`; wrapper exit 0, timeout false; all three rows were recorded complete.
- Private mount namespace/tmpfs checks passed, host WSLg socket metadata was unchanged, and all three Xvfb instances exited naturally with status 0. Initial/final layout readbacks matched; both mapping actors ran in-window and exited 0.
- The fixture received a pointer click and Tk passive logs include the initial `a` and post-wait second-text keys. However, no row produced the independently saved `effect.json`; save chord effects were absent when sampled. Backend dispatch reported completed with operations 0–8 and verified releases, but the independent effect evidence is missing.
- The single frozen auditor returned `STOP_PROVENANCE_OR_RUNNER`, citing absent control effect and absent completed effects for both remap rows. The five frozen mutation controls all rejected their changes; changed output was classified `FAIL_STALE_MAP_EFFECT`.
- Full `raw.json`, `wrapper.json`, actor receipts, fixture metadata and Xvfb logs are preserved. No Xvfb, fixture, or actor process remains.

Classification: immutable `STOP_PROVENANCE_OR_RUNNER`; this does not establish a scientific result. One possible harness gap is that the fixture is torn down immediately after Ctrl-S, before a separately recorded post-save event-loop wait. That hypothesis may only be investigated in an additive successor with a new output allocation and freeze.

