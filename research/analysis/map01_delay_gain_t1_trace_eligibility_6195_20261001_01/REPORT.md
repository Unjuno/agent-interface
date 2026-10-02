# Issue #6195 T1 retained-trace eligibility — allocation 02

## H / T / D / C / U

- **H:** One of exactly two retained v38/v39 event logs may contain the identity-joined same-clock evidence needed for a causal delay×policy T2. The test is eligibility only; missing trace fields are not live-system evidence.
- **T:** Frozen read-only JSONL inventory; candidate once; independent raw-only audit once after candidate exit 0; five candidate corruption controls.
- **D:** Candidate emitted `HOLD_NO_CLOSED_LOOP_TRACE` (2 examined, 0 eligible). Candidate ran 19:35:22–19:35:24 UTC, exit 0. Auditor ran 19:36:02–19:36:04 UTC, exit 0, reconstructed both summaries and rejected 5/5 mutations.
- **Integrity:** The registered allocation is `MAP01-DELAY-GAIN-TRACE-ELIGIBILITY-6195-T1-20261001-02`, but both candidate and auditor emitted/expected allocation-01. The auditor did not bind that identifier to FREEZE and therefore cannot authenticate this as allocation-02. Final package disposition: `FAIL_ALLOCATION_BINDING_AUDIT_GAP; DATA_HOLD_NO_CLOSED_LOOP_TRACE`. Both raw files remain unchanged; no retry or repair.
- **C:** The explicit field/event rubric can conservatively miss semantically equivalent encoding. Candidate/auditor agreement on a stale hard-coded run ID demonstrates why reconstruction plus mutation rejection does not itself authenticate allocation identity.
- **U:** No actual input occupancy, independent useful feedback, closed-loop stability, causal delay effect, GUI/DOOM safety, task effect, MAP01 success, human tempo, or runtime/product claim.

## Result detail

V38: 340 events, 238 capture rows, zero consumed-generation values, zero effects, zero verified identity-bound release rows; only source capture passed. V39: 634 events, 436 capture rows, zero consumed-generation values/effects, one release row not joined to its 28 held rows; only source capture passed. Each trace failed the other five of six endpoint gates. Candidate raw SHA-256 `b0f39d27d1ef44dd14007286f5e09caf8c0a5e00bc3be25514a0bdf8d8699060`; audit raw SHA-256 `688eb115c146544e85dd08e20ee0706f352669f0c37bc6684c79c2abdc8f8988`.

## Execution context

Main `14b81dd1f6853623a694266b98538f812847257a`; branch `research/6195-delay-gain-t1-trace-eligibility-20261001-02`; CPython 3.11.9 on local Windows host CPU. No GPU/CUDA, model, Docker/WSL, network during execution, GUI/game, app, input or task effect. Full raw and invocation records are under `outputs/MAP01-DELAY-GAIN-TRACE-ELIGIBILITY-6195-T1-20261001-02/`; exact input provenance is pinned in `FREEZE.json`.
