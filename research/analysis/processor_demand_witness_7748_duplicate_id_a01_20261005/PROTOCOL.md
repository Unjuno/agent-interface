# Issue #7748 duplicate-job-ID boundary A01

## H / T / D / C / U

**H.** In the finite single-processor demand diagnostic, every job identifier must be a unique nonempty string. A duplicate identifier can collapse per-job remaining-work bookkeeping and corrupt policy-miss attribution; it must return `HOLD_DUPLICATE_JOB_ID` before demand or schedule calculations. Empty or non-string IDs must return `HOLD_NO_SCHEDULABILITY_INPUTS`. Recognized, distinct-ID cases must preserve their frozen outputs.

**T.** Apply the strict identity gate to three frozen cases: a feasible workload whose best-effort-first policy misses a control deadline, a control-feasible but jointly infeasible workload, and the same first workload with the best-effort job assigned the control job's ID. An independent raw-only auditor separately validates identity eligibility and recomputes interval demand plus exhaustive unit-slot feasibility. Construction controls mutate the duplicate row to `ELIGIBLE`, alter its ID after candidate output, omit it, and use an empty/non-string ID. Compare the duplicate-ID result against the unmodified #7748 predecessor candidate as a read-only regression witness.

**D.** `PASS_DUPLICATE_ID_BOUNDARY_SCOPED` only if both distinct-ID fixtures retain their frozen classifications, the duplicate fixture is held before calculations by candidate and auditor, malformed identifiers are held, the predecessor canary reproduces `FEASIBLE_NO_POLICY_MISS` in place of `POLICY_MISS_ON_FEASIBLE_TRACE`, and the raw-only auditor rejects duplicate-ID acceptance, post-candidate identity mutation, and omitted rows. Any duplicate accepted as eligible or valid case drift is `FAIL_METHOD`; provenance or runtime mismatch before formal invocation is `STOP_PROVENANCE_OR_RUNTIME`.

**C.** A policy simulator could avoid key collisions by representing jobs positionally, but duplicate external IDs would still make the input ambiguous and schedule receipts non-joinable. A future model may define composite identity; this test does not invent one.

**U.** Three authored traces and an integer-tick single-processor model only. No general schedulability, full CBS, host/container timing, GUI, Agent Interface runtime/resource, safety, or physical-release claim. Candidate and auditor are separate implementations by one author, not independent human review.

## Frozen execution boundary

Allocation: `7748-DUPLICATE-ID-A01-20261005-01`. Formal budget: one candidate invocation, then one raw-only auditor invocation only if the candidate exits zero; retries zero. Run the pinned no-network OrbStack image only if the engine can identify the image and launch successfully. The read-only image inventory currently fails on a missing content-store blob (`operation not supported`); if that remains true, run the deterministic standard-library case on host CPython and claim no container isolation or resource enforcement. Preserve the first environment observation. Do not modify or rerun #7748/#7762/#8061 results.

Candidate command:

```sh
python3 -B research/analysis/processor_demand_witness_7748_duplicate_id_a01_20261005/candidate.py --output research/analysis/processor_demand_witness_7748_duplicate_id_a01_20261005/results/candidate.raw.json
```

Auditor command:

```sh
python3 -B research/analysis/processor_demand_witness_7748_duplicate_id_a01_20261005/audit.py --raw research/analysis/processor_demand_witness_7748_duplicate_id_a01_20261005/results/candidate.raw.json --output research/analysis/processor_demand_witness_7748_duplicate_id_a01_20261005/results/AUDIT.json
```
