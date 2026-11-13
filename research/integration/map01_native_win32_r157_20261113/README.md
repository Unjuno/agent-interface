# MAP01 native Win32 R157 — independent neutral horizon

Date: 2026-11-13  
Classification: **PASS for the preregistered single-run release/task gates; PASS_SCOPED_NO_RECORDED_FORWARD_COMMAND for the retained demo audit.**  
This is one instrumented native-Windows observation. It is not a reliability estimate, MAP01 completion, application-queue quiescence proof, or a speed comparison.

## Question and frozen conditions

R157 tested the current public compiled-supervised Win32 caller after R156's missing held-sample/resolver join. It kept expiry-boundary samples separate from pending-call resolver polls, required exact-call reconciliation, observed an independent two-second same-generation neutral input horizon, and retained the separate numeric ammo task oracle and same-run demo audit.

- Attempt: `map01-native-fresh-capture-r157-20261113`
- One fresh GZDoom MAP01 process and exactly one public dispatch; no retry or replay.
- Frozen source candidate: `7242fe020b18b28d26818fb7367857cba2da3c05`, a documentation-only commit directly on `origin/main` `195fc6cdd2b1f30396fd5c846225c7fb04c172b4`. The live run was therefore on the clean task branch, not the main ref named in the preregistration. The pinned runtime and research helper hashes matched the main-base tree; this provenance deviation is retained rather than relabeled.
- Frozen conditions SHA-256: `181e50e1d03b783f449f91a5a8477a9712a6229490176f8c05c2106f64a2d54b`.
- Post-freeze verification passed all 60 checks. Before the live run, focused local checks passed: evidence join 3/3, neutral horizon 5/5, packet adjudication/timing/contract 10/10.
- The task-local packet is `private-packets/map01_native_windows_deep_trace_20261113_r157/`. Its post-run manifest covers 105 files with zero mismatches. The later additive demo adjudication is covered by `R157_ADJUDICATION_ADDENDUM_SHA256SUMS.json`, whose parent is the verified post-run manifest.

## Live result

- The expiry sampler independently saw W still down in its first fully post-deadline sample, then fully up by the first up sample at **10.7525 ms after expiry**. The conservative outer read bracket was **12.0785 ms**, below the frozen 20 ms bracket limit. The sampled post-deadline down duration was 9.9999 ms; no read error or unknown sample occurred.
- The public call resolved by exact call ID `2dc7cbc4f1764cd6a4fe8eb6ab862ea4`; operation `b66517b06d594b21a661793a8cba073a` ended `recovered`, with `release_confirmed=true` and replay denied. The public recovery receipt arrived 22.2522 ms after the expiry timestamp; that receipt time is reported separately from the passing sampler bracket.
- The recovery's own late-input horizon covered 2 seconds with 75 observations and a maximum observed gap of 33.6113 ms. A separate caller-side horizon then verified continuous neutral W and left mouse for 2 seconds on the unchanged exact process and target generation: 181 observations, max sample gap 12.0063 ms.
- The caller remained `SAFE_YIELD/delivery_uncertain`. Its independent same-run oracle classified ammo **50→49**, and the public task receipt matched the exact dispatch, operation, and target generation with `task_success=true`. These are scoped task-effect evidence, not a claim that the graph itself completed the task.
- The retained demo audit returned `PASS_SCOPED_NO_RECORDED_FORWARD_COMMAND`: no recorded forward-command tics after expiry before release or after release through the complete recovery horizon. This does not exclude queued Windows messages, other input types, or scheduled effects.
- All 18 R157 decision checks and all 4 demo-audit conditions passed. The owned GZDoom exited normally (exit 0; no forced termination); custody is clear at revision 437.

## Interpretation and remaining boundary

This run confirms the R156 evidence-join repair on the normal pending-resolution path, including separate expiry and resolver provenance, exact-call release reconciliation, task-oracle linkage, and the independent neutral horizon. It does **not** exercise R157's runner exception-reconciliation branch: the resolver returned normally, so the exception-only fallback remains unverified. That is the next finite local task: inject terminal resolver/result-query failures into a deterministic integration harness and verify exact-call-only reconciliation, no replay, and conservative UNKNOWN handling before attempting another live run.

The demo result says there was no recorded delayed W-forward command in this run's scoped interval. It cannot establish that the OS/application queue is empty. R149's distinct fixture result still demonstrates that task effects can appear after an input-neutral horizon; input release and application effect must remain separate. No speed claim follows from R157; #57's matched same-model/all-attempt comparison remains open.

## Preparation defects found and repaired

The R157 freeze script had a tautological runtime comparison and attempted to pass raw bytes to a path-only hash helper. Both were repaired before the conditions freeze. The first freeze also correctly stopped while the requested plan was uncommitted; committing the plan produced a clean worktree before freezing. The standalone demo adjudicator requires the repository helper directory on `PYTHONPATH`; the successful retained audit used that path without changing frozen experiment files.

## Evidence

Raw trial data, exact conditions, source/asset pins, execution logs, reports, and manifests are retained in the task-local packet above. The commit tested/frozen and the live-run source pins are recorded in `conditions.json`; the repository-facing source tree and this result summary do not replace those raw files.

