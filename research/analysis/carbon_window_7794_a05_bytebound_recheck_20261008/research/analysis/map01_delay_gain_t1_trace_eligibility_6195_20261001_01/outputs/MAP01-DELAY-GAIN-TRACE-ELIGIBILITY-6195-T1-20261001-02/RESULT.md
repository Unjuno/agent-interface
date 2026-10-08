# Issue #6195 T1 allocation 02 result

## H / T / D / C / U

- **H:** At least one retained v38/v39 trace has all six source→decision→held-action→release→effect/clock/repeated-correction eligibility gates. Otherwise these logs cannot support #6195's causal delay×policy T2.
- **T:** Frozen read-only inventory of exactly two Git-blob-pinned JSONL files; one candidate run, then one independent raw-only audit and five mutation controls.
- **D:** Candidate reports `HOLD_NO_CLOSED_LOOP_TRACE`: 2 traces examined, 0 eligible. Candidate exit 0 at 19:35:22–19:35:24 UTC. Auditor exit 0 at 19:36:02–19:36:04 UTC; it reconstructed both summaries and rejected 5/5 mutations. However, both scripts emitted/expected allocation-01 while the registered allocation was allocation-02. The auditor did not bind the emitted allocation identity to FREEZE; its PASS is only reconstruction-scoped.
- **Final disposition:** `FAIL_ALLOCATION_BINDING_AUDIT_GAP; DATA_HOLD_NO_CLOSED_LOOP_TRACE`. The raw candidate indicates no eligible trace, but this package is not an allocation-02-valid PASS or a T2 authorization. Preserve both outputs unchanged. No retry or code repair.
- **C:** The field/event rubric may miss semantically equivalent evidence encoded under different names; none is inferred here. The candidate/auditor's shared stale allocation literal shows that reconstruction and mutation rejection alone do not authenticate allocation identity.
- **U:** No conclusion about actual physical key occupancy, live controller stability, useful feedback, task-effect causality, GUI/DOOM safety, MAP01 success, human tempo, or runtime performance.

## Frozen context and raw identities

Main `14b81dd1f6853623a694266b98538f812847257a`; allocation `MAP01-DELAY-GAIN-TRACE-ELIGIBILITY-6195-T1-20261001-02`; branch `research/6195-delay-gain-t1-trace-eligibility-20261001-02`. Candidate SHA-256 `aa1c0b74f825c3f11405903c3a61a4a4e7573924b54a3b828a117c5cd5b9b699`; auditor SHA-256 `ec92b8ec117997cb2d6a8ba2720d6119a24569a0417116b443ac74c225b4d32a`. Candidate raw SHA-256 `b0f39d27d1ef44dd14007286f5e09caf8c0a5e00bc3be25514a0bdf8d8699060`; audit raw SHA-256 `688eb115c146544e85dd08e20ee0706f352669f0c37bc6684c79c2abdc8f8988`.

Inputs are exactly the frozen v38/v39 raw logs (308,873 / 565,849 bytes); their Git blob IDs and raw SHA-256 values remain in `FREEZE.json`. Execution used Windows host CPython 3.11.9 and read-only local CPU processing. No model, GPU/CUDA, Docker/WSL, GUI/game, application, input, or task effect.
