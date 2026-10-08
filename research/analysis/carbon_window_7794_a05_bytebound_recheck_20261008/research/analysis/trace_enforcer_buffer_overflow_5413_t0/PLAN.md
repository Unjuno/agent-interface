# Issue #5413 T0: bounded trace-buffer overflow boundary

## Status and scope

One host-CPU construction experiment. This is not the shared Docker/OrbStack
formal allocation and must not be reported as a container result. It tests one
finite synthetic boundary in the Issue's stated buffer-overflow requirement.

## H / T / D / C / U

- **H:** A trace enforcer that silently drops an overflowed evidence event can
  admit a commit whose target was invalidated by that event; converting any
  overflow to an explicit UNKNOWN prevents that admission, at the cost of
  conservatively blocking even an overflow consisting only of irrelevant
  telemetry.
- **T:** Run one deterministic 3-case x 2-policy matrix: exact matching evidence
  without overflow; an external target mutation as the third evidence event
  beyond capacity 2; and irrelevant telemetry as the third event. Compare
  `FAIL_CLOSED` against an explicitly unsafe `DROP_NEWEST` baseline. One
  independent raw-only auditor recomputes decisions from full input rows, then
  five corruption controls must all be rejected. No RNG, model, GUI, network,
  task effect, or timing claim.
- **D:** `PASS_CONSTRUCTION_ONLY` only when four construction tests pass; the
  frozen 6-cell runner emits exactly one row per case/policy; the independent
  audit accepts the raw matrix with zero errors; the mutation-overflow baseline
  admits the stale commit while `FAIL_CLOSED` returns
  `UNKNOWN_BUFFER_OVERFLOW` without effect; and all 5/5 corrupted matrices are
  rejected. `FAIL` if the proposed policy emits that effect or a corruption is
  accepted. `UNCERTAIN` if the bounded model does not discriminate policy
  behavior or its hand-authored event semantics do not represent real buffer
  operation.
- **C:** A buffer could preserve invalidation events preferentially or use a
  compact monotone invalidation watermark, avoiding the telemetry false reject
  without a blanket overflow hold. The finite test does not compare those
  designs.
- **U:** The queue, event identities, and effect gate are synthetic and fully
  observed. No real buffer implementation, GUI timing, partial-observation
  channel, intent distance, or task-effect semantics are exercised. This does
  not establish runtime safety or practical utility.

## Frozen source and execution

- GitHub `main` base at fetch: `bc57d55d4e0a4e75d1945d541ed27fce7cb2b955`.
- Local branch: `research/5413-buffer-overflow-t0-20261001`.
- Python: host CPython 3.14.5; standard library only.
- Construction command, already executed before this freeze: `python3 -B -m unittest discover -s research/analysis/trace_enforcer_buffer_overflow_5413_t0 -p 'test_*.py' -v` (4/4 PASS).
- Frozen source SHA-256:
  - `experiment.py`: `aadc5eb5007032c841973be68807a75acf1b3c37723bf9cf16a220a1e2025f3b`
  - `audit.py`: `adc675afdebea50802f063cebe822b25d7d1fd72ee953a8748b5d3de5f9a8699`
  - `corruption_controls.py`: `63e35b4806148d7e406f8e544aab844506fca1242c08b388caca071cd4821634`
  - `test_experiment.py`: `055a9686f4101da1ab83b4025dec3e5f3c31fe14836d5876864d8c9ae20dbf52`
- Formal Docker allocation: **not requested/granted; invocation count 0**.
- Frozen host runner command: `python3 -B research/analysis/trace_enforcer_buffer_overflow_5413_t0/experiment.py > research/analysis/trace_enforcer_buffer_overflow_5413_t0/raw/host-formal-01.jsonl`.
- Then run the independent auditor once on that file, followed by its five
  corruption controls. Do not edit frozen sources or rerun the candidate.

## Local result boundary

Even a passing host run is only a deterministic construction result. A Docker
run, repository local CI, GitHub Issue report, reviewable PR, and merge are
separate not-yet-satisfied gates.
