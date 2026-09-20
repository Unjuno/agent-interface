# #3300 scorer smoke — 2026-09-20

Disposition: `PASS_SCORER_CALL_PATH_ONLY`; issue-level disposition remains `HOLD_LIVE_SPAN_UNIDENTIFIED`. This is excluded construction evidence, not a formal allocation.

## H/T/D/C/U

- H: the exact current-main `_coherent_progress_sample` can be loaded from an OrbStack container with the pinned ViZDoom package and retained MAP01 fixture, and its call outcome/span can be captured without modifying the scorer.
- T: one `linux/arm64` OrbStack container, `--network none`, image `sha256:8d984b04efe5bca7bd9b3808aac4f56bd273a6a1ada76cd51939253b874244ca`; ViZDoom 1.3.0, `ASYNC_SPECTATOR`, 35 Hz, fixture manifest SHA-256 `e57e21fd6d85d4b0720b3b3d5a52ad538fde45c50c58651ff754638f93f182e`, save SHA-256 `cc5302aa9cda3960248733caa96da1b53adcc4b6a1a2dcfb80675650c9350401`. After load, one explicit startup `advance_action(1, True)` was followed by ten exact scorer calls separated by 50 ms wall-clock waits. No model, network, human input, or Doom action vector was used.
- D: all 10/10 scorer calls returned; outer-call spans were 49,203–218,681 ns. Every pre-call tic read was 1367. Raw rows are in `scorer_smoke.jsonl`; summary is `scorer_smoke_summary.json`.
- C: this PASS is only exact scorer import/call-path and raw timing capture on the static loaded fixture. It does not establish tic progression, actual three-attempt raw bracket spans, inter-attempt timing, phase offsets, load strata, all-three failure probability, or live async coherence. No formal rows are counted.
- U: a non-perturbing and preregistered method to obtain a continuously advancing MAP01 clock while preserving the exact frozen three-attempt predicate and sampling boundary remains unresolved. Issue #3300 requests that live boundary; no fresh input/action policy is introduced here.

Raw SHA-256: `da37e019005505a137726d230a46870c2de5ca7db31839f924e160645e7a4375`.
Summary SHA-256: `07fff2da622f8caab9db3a2090a14f05216ec0882fc5d83b5cb4dfa363d4c4d0`.

The smoke runner is `scorer-smoke.py`. No previous artifact or result was modified.
