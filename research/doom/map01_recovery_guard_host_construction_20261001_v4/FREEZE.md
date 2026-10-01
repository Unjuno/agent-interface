# Freeze: host-only recovery guard construction

- Allocation: HOST-59-RECOVERY-GUARD-C-20261001-04
- Owner: current Windows Codex task; host CPU only
- Base main at branch creation: 686ae6c94dd67e78bab9920457085dc6ad1ced19; GitHub compare confirmed branch identical to main (0 ahead / 0 behind)
- Frozen protocol path: research/doom/map01_recovery_cover_matched_v2_runner_3211_diagnostic_v2.py
- Frozen protocol Git blob SHA-1: f5caf71a743a563b7de046b82d44db7ebe49e829
- Exact protocol bytes: frozen_source.b64, fetched from the allocation branch with GitHub MCP
- H: Fresh sequence with observed health >= source health continues; stale sequence, unavailable health, and health loss reject.
- T: Syntax/preflight checks, then one host-only invocation on four predeclared cases; one separate raw-only audit only if candidate exits 0. Also verify recovery-step shape and freshness deadline.
- D: PASS_HOST_GUARD_CONSTRUCTION iff all four frozen cases match and bounds hold. PASS_HOST_RAW_AUDIT iff independent reconstruction passes with 5/5 mutations rejected. Source/output mismatch is STOP before candidate.
- C: CPython standard library; no container, network, model, GPU/CUDA, game, GUI/X11, user input, or live task. No random seed.
- U: Pure predicate construction only; not cancellation/release ordering, MAP01 threat survival, or integrated-runtime evidence.
- The live #59 isolated-container T1 is separate and still unassigned; this allocation is host-only and is not a lease.
