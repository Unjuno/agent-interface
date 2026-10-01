# Freeze: host-only recovery guard construction

- Allocation: HOST-59-RECOVERY-GUARD-C-20261001-03
- Owner: current Windows Codex task; host CPU only
- Base main at branch creation: 32cac82ec1f5b6e79035d8022a125b785218c897 (compare main vs branch: identical, 0 ahead / 0 behind)
- Frozen protocol path: research/doom/map01_recovery_cover_matched_v2_runner_3211_diagnostic_v2.py
- Frozen protocol Git blob SHA-1: f5caf71a743a563b7de046b82d44db7ebe49e829
- Exact bytes: frozen_source.b64 fetched from the allocation branch at this base ref
- H: A fresh sequence with observed health at least source health continues; stale sequence, unavailable health, and health loss reject.
- T: One host-only invocation of the pinned pure predicate on four predeclared cases, then one separate raw-only audit only if candidate exits 0. Also verify bounded recovery-step shape and source-freshness deadline behavior.
- D: PASS_HOST_GUARD_CONSTRUCTION iff all four frozen cases match and bounds hold. PASS_HOST_RAW_AUDIT iff independent reconstruction passes with 5/5 mutations rejected. A source/output mismatch is STOP before candidate invocation.
- C: CPython standard library; no container, network, model, GPU/CUDA, game, GUI/X11, user input, or live task. No random seeds.
- U: Pure predicate construction only; not cancellation/release terminal ordering, MAP01 threat survival, or integrated runtime evidence.
- Live #59 container T1 is separate and still requires its own explicit exclusive slot; this host construction does not request or imply one.
