# Issue #7748 duplicate-job-ID boundary A02

## H / T / D / C / U

**H.** In the finite single-processor demand diagnostic, every job identifier must be a unique nonempty string. Duplicate identifiers must return `HOLD_DUPLICATE_JOB_ID` before demand or schedule calculations. Empty/non-string identifiers hold. Distinct-ID frozen cases retain their prior classifications.

**T.** Apply the identity gate to the same three frozen cases as A01: feasible policy-miss canary, control-feasible but jointly infeasible workload, and duplicate-ID variant. The raw-only auditor checks identity eligibility and recomputes interval demand plus exhaustive unit-slot feasibility. A02 is an independent allocation after A01 stopped because its auditor wrote a scoped PASS JSON but returned exit 1. The only methodological/code delta is correcting the auditor CLI success mapping from the predecessor class-boundary status to `PASS_DUPLICATE_ID_BOUNDARY_SCOPED`; the raw schema is versioned to A02. A01's STOP and outputs are preserved and are neither changed nor pooled.

**D.** `PASS_DUPLICATE_ID_BOUNDARY_SCOPED` only if both distinct-ID fixtures retain frozen classifications, duplicate IDs hold before calculations in candidate and auditor, malformed IDs hold, predecessor canary reproduces the duplicate-ID misclassification, and raw-only auditor rejects duplicate acceptance, post-candidate identity mutation, and omitted rows. The CLI must return 0 exactly for auditor PASS and nonzero for failure. Any method mismatch is `FAIL_METHOD`; provenance/runtime mismatch before formal execution is `STOP_PROVENANCE_OR_RUNTIME`; candidate/auditor status-exit mismatch is `STOP_AUDITOR_EXIT_MISMATCH`. One candidate invocation and one auditor invocation maximum; no formal retries.

**C.** Positional bookkeeping could avoid internal key collision, but duplicate external IDs remain ambiguous and receipts cannot be reliably joined. This boundary requires uniqueness; no composite identity is inferred.

**U.** Three authored traces and an integer-tick single-processor model only. No general schedulability, full CBS, host/container timing, GUI, Agent Interface runtime/resource, safety, task-effect, or physical-release claim. Candidate and auditor are separate implementations by one author, not independent human review.

## Frozen execution boundary

Allocation: `7748-DUPLICATE-ID-A02-20261005-01`. Frozen main: `3c2254ddc4446bec9a8ab4871ed05defa0a900f9`. The Docker/OrbStack read-only image inventory failure was observed and preregistered for A01; this standard-library-only scoped model uses the same host-only CPython 3.14.5 fallback, without isolation/resource-enforcement claims. Do not repair shared OrbStack or change A01.

Candidate, once:

```sh
python3 -B research/analysis/processor_demand_witness_7748_duplicate_id_a02_20261005/candidate.py --output research/analysis/processor_demand_witness_7748_duplicate_id_a02_20261005/results/candidate.raw.json
```

Auditor, once and only if candidate exits 0:

```sh
python3 -B research/analysis/processor_demand_witness_7748_duplicate_id_a02_20261005/audit.py --raw research/analysis/processor_demand_witness_7748_duplicate_id_a02_20261005/results/candidate.raw.json --output research/analysis/processor_demand_witness_7748_duplicate_id_a02_20261005/results/AUDIT.json
```
