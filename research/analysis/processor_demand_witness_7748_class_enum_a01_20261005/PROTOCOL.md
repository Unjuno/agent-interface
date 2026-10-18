# Issue #8061 — frozen class-enum boundary experiment

## H / T / D / C / U

**H.** A strict finite job-class schema (`control`, `best_effort`) preserves expected decisions for recognized jobs, while every missing, malformed, or unrecognized class returns `HOLD_UNKNOWN_JOB_CLASS` before any control-only demand calculation. In particular, a safety-critical job with an unknown label cannot be silently omitted and make an overloaded control-only set appear feasible.

**T.** Allocation `7748-CLASS-ENUM-A01-20261005-01` is a finite integer-tick, preemptive, unit-speed, one-CPU method test. The seven frozen cases cover recognized mixed-class feasibility, control-feasible/joint-overload separation, unknown `safety_critical`, misspelled `contorl`, missing, null, and non-string labels. Construction tests run before source freeze. Freeze current `main`, this protocol, cases, candidate, independent raw-only auditor, tests, environment and predecessor inputs/sources. Then invoke the candidate once and the raw-only auditor once; retries are zero. The candidate schedules by discrete EDF; the auditor uses interval-demand feasibility plus exhaustive slot-state enumeration and imports no candidate code. Run on a pinned no-network OrbStack image if OCI execution works. If the container preflight fails, this standard-library-only model may run on the recorded host as explicitly permitted by #8061; no isolation/resource-enforcement claim follows.

**D.** `PASS_CLASS_BOUNDARY_SCOPED` requires literal hand-checked outputs for both recognized-class fixtures, HOLD for every unknown/malformed class before eligibility, agreement of the auditor's interval and exhaustive feasibility oracles on every eligible row, and rejection of unknown-class-result, class-substitution and omitted-row mutations. `FAIL_CLASS_ACCEPTED` if any unknown/malformed class is ELIGIBLE or silently excluded. `FAIL_AUDIT` for an oracle disagreement or accepted corruption. `STOP_PROVENANCE_OR_RUNTIME` before candidate invocation for any frozen identity mismatch. Preflight/container STOP is retained independently and never converted into a container PASS.

**C.** A versioned enum or explicit unsupported-class bucket may be preferable to a closed enum. New legitimate classes must require an explicit schema update; the fail-closed outcome is a HOLD, not a safety judgment.

**U.** Seven authored rows establish only this bounded parser/auditor boundary and finite synthetic schedule behavior. They do not implement full CBS, prove general schedulability, identify a corresponding runtime resource, or establish OS/container timing, GUI behavior, safety, or physical key release. Candidate and auditor are separate implementations by one author, not independent human review.

## Preservation and invocation boundary

Do not modify or rerun Issue #7748 / PR #7762 candidate, formal result, auditor result or hashes. Do not alter Issue #7778's slack-reclamation outcomes. Formal candidate calls: exactly 1. Formal auditor calls: exactly 1. Formal retries: 0. Construction tests may run before freeze and are not formal invocations. Keep all outputs additive under this directory.

## Frozen formal commands

```sh
python3 -B research/analysis/processor_demand_witness_7748_class_enum_a01_20261005/candidate.py --output research/analysis/processor_demand_witness_7748_class_enum_a01_20261005/results/candidate.raw.json
python3 -B research/analysis/processor_demand_witness_7748_class_enum_a01_20261005/audit.py --raw research/analysis/processor_demand_witness_7748_class_enum_a01_20261005/results/candidate.raw.json --output research/analysis/processor_demand_witness_7748_class_enum_a01_20261005/results/AUDIT.json
```

The frozen runner identity and exact output hashes are recorded after those single invocations in `RUN.json` and `SHA256SUMS`.
