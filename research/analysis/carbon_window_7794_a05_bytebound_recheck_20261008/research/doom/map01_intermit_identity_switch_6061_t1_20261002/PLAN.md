# Identity-switch control gate — Issue #6061 T1

Allocation: INTERMITTENT-IDENTITY-SWITCH-6061-T1-20261002-01

## H / T / D / C / U

**H.** A kinematic predictor with near-zero motion error can continue a bounded motor chunk after the semantic target has changed. A separately checked, current identity/evidence-epoch fence should release at the first observable mismatch or missing identity evidence. If the semantic switch is observationally indistinguishable from the unchanged-target control, the result must remain UNKNOWN, not receive predictor credit.

**T.** Five deterministic 12-tick traces, four policies, 20 trajectories: unchanged-target control; visible identity+epoch switch; stale identity label with epoch-only change; missing identity+epoch; and a silent semantic switch whose planner-visible observations exactly equal the unchanged-target control. Every motion-prediction error is 0.0. Policies are identity+epoch gate, identity-only gate, kinematic-only ablation, and one-tick no-continuation baseline. Candidate receives only input.json; independent scorer alone receives truth.json. Construction suite runs before freeze. Freeze source/input/image and output absence, then invoke one candidate and one independently implemented raw-only auditor in one network-disabled, read-only-root OrbStack container, each exactly once and no retry.

**D.** Scoped method gate passes only if the full gate releases exactly at tick 5 in the three cases with observable identity, epoch, or unknown-state change; it issues no command after that boundary; identity-only misses the epoch-only switch; the kinematic-only ablation misses the observable changes; five corruption controls are rejected; and the silent-switch/control traces are identical and disposition is UNKNOWN_NOT_CREDITED. The overall disposition is HOLD_SILENT_IDENTITY_SWITCH_UNOBSERVABLE if the silent case remains indistinguishable, not a policy win. Any gate miss or audit disagreement is FAIL. No live allocation is consumed.

**C.** The fixture has exact synthetic currentness fields and a perfect one-dimensional probe. An independently available real identity/epoch receipt may not exist in actual GUIs; bounded chunking or no continuation may be preferable where that signal is absent. CPU scheduling and capture cost are not measured.

**U.** This does not establish physical input occupancy/release, a real runtime guard, task effect, safety, live MAP01 behavior, human tempo, GUI transfer, or product benefit. The synthetic hidden-truth switch is used only by the auditor; a silent switch cannot be detected from identical observations.

## Preparation record

An early test command used module-style unittest invocation before the test file was in the correct worktree and exited during discovery; a subsequent discovery command from the wrong directory found zero tests. Neither invoked a formal candidate/auditor or container. After path correction, the intended construction suite passed 8/8. Preserve these as preparation/invocation mistakes, not hypothesis outcomes.
