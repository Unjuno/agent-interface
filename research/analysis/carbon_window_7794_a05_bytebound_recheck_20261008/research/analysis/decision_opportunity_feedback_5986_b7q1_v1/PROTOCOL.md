# Issue #5986 — decision-opportunity feedback T0

**Scope:** one finite synthetic measurement-method test. No route, model, GUI, user, safety, or product claim is made.

## H / T / D / C / U

**H.** A decision-opportunity label that binds source event, capture, delivery, generation, eligibility deadline, decision change, and independent synthetic effect will reject arrival-only or relevance-only false positives. It will never count undelivered/post-deadline/stale feedback as verified value and will never permit a mandatory safety cue to be withheld.

**T.** Six fixed cases with byte-identical optional cue content for early, late, undelivered, redundant, and stale-generation controls; a distinct mandatory safety cue is always delivered. Candidate emits the three simple comparator labels and the stricter opportunity taxonomy, explicit source/capture/delivery/deadline timing, action-change/effect diagnostics, and observation/delivery/processing cost. A separate raw-only auditor reconstructs each row and checks five effective output corruptions. Candidate once, then auditor once only if candidate exits 0. No retries.

**D.** `METHOD_PASS_SCOPED` only if the six frozen classifications match, no row claims verified value (a synthetic effect delta remains diagnostic), the stale case yields, safety is ineligible for withholding and reaches every arm, timing/cost fields independently reconstruct, and all five corruptions reject. Otherwise preserve the first FAIL/STOP/HOLD. This T0 tests taxonomy/accounting, not causal empirical feedback value.

**C.** The only data are the six hand-authored rows in `fixture.json`. The first five use the same source-bound cue string/event identity; the sixth uses a distinct hazard cue. Timings, decisions, action eligibility and effects are synthetic oracle fields; they are not observations from #503, #3700, a GUI, model or human. All time values share one declared synthetic clock. No old run, data, seed, branch or output is reused.

**U.** Whether earlier feedback changes a real bounded agent's choice; matched human/agent time; route/task benefit; cue interpretation; model latency; app effects; confidence or population generalization remain unknown. T1 requires a new prospective disposable-fixture allocation and is outside this run.

## Reproducibility / execution

Issue source #5986 read at main `3adec9cdc2cff5ef68f19acd55c5823fcaad26df`; r133 still requests true held-input occupancy, independent first useful feedback, bounded recovery, and transfer without new model/GUI calls. Main now also documents the existing live primary-feedback API in `runtime/host_v1/FEEDBACK.md`; this T0 does not claim or retest that runtime path. Own branch `research/decision-opportunity-feedback-5986-t0-20261002-b7q1`. Allocation `DECISION-OPPORTUNITY-5986-T0-20261002-01`; owner local Windows Codex task `01a0b990-3d17-72f1-a908-9a2072104ce5`. Planned exclusive one-shot window: 2026-10-01 15:45–16:05 UTC. Freeze source and hashes before candidate execution; output path `outputs/DECISION-OPPORTUNITY-5986-T0-20261002-01/` must be absent.

This arithmetic T0 requires only local CPU. A read-only `docker ps --all --no-trunc` inventory query timed out after five seconds; the existing Docker/WSL shared-runtime state remains unknown, so this run will not start or touch a container. GPU/CUDA and model loading are not relevant to the finite method question. No package installation, model/network call, container, GUI, OS input, or user data is used.
