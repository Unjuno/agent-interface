# Issue #6749 successor T0 — result

Final disposition: `PASS_METHOD_SCOPED`. One WSLc candidate emitted 8,640 prefix rows; one independent raw-only WSLc auditor reconstructed all 8,640 rows with no errors and rejected all five preregistered corruptions. Formal invocations were candidate=1, auditor=1, retries=0. The immutable raw SHA-256 is `12aa81b815bf7d92bca7d8b6b315c50c1377385c002ce609ccbb0abd8a111a6ba`; audit JSON SHA-256 is `f0555d9bb17b97068a70a9a0521594f31c7c372d97210fda7b866fc201a99f7c`. Exact stdout, exit, commands, image IDs, and warning are retained in `formal_01_20261003/`.

Disposition counts: `INVALID` 2,160; `PASS` 60; `PROVISIONAL` 5,250; `STABLE_FAIL` 1,170. These sum to 8,640. The `disposition_counts` object contains only these labels; `early_finalization_metrics` is separately keyed. Every stable-negative row retains any not-yet-arrived mandatory check and source-frontier obligation. The five rejected corruptions were: drop pending mandatory, forge optional completion, mix metric into disposition counts, relabel invalid generation as current, and treat timeout as complete. External effects/authority: 0.

Construction checks passed 7/7 twice; they are distinct from the one-shot formal allocation. WSLc reported cgroup/swap support unavailable, so the requested 512 MiB was not treated as verified enforcement. The formal result is finite-model method evidence only.

The original #6689 T0 and #6704/#6706 successor findings remain preserved and unchanged. This is a fresh successor allocation from main `25532de0bf5dca01901150eb2ea0799f86ff4c56`; it does not pool earlier raw data.

Issue #6749 initially names OrbStack. Per the user's explicit instruction, this allocation uses WSLc. This engine amendment is disclosed and does not claim cross-engine equivalence. The model is finite, deterministic, CPU-only, offline, and uses no engine-specific capability.

The protocol requests one CPU and 512 MiB. WSLc emitted its cgroup/swap unsupported warning during construction; effective memory enforcement is unverified and is not claimed. No GPU, model, GUI, provider, task/user data, runtime edit, authority, or external effect is involved. Method-scope and realism limits are in `PREREGISTRATION.md`.
