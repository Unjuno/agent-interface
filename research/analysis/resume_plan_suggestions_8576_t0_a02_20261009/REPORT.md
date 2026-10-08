# T0 A02 result — executed mutation-gate requalification

## Disposition

`PASS_METHOD_SCOPED` for this finite synthetic method fixture. The candidate ran once and exited 0; the frozen independent auditor ran once and exited 0. The auditor reconstructed 12/12 expected rows with zero errors and **executed all six named mutations**, rejecting each with a recorded validation reason. The result closes only the specific evidence gap in A01's mutation-count gate for this new allocation. A01's aggregate PASS remains unsupported under its original protocol; its raw and frozen files are unchanged and were not rerun.

The equal-public-input pair (`paired_hidden_a` / `paired_hidden_b`) produced the same checkpoint and provenance decision despite different hidden labels. Ambiguous, stale, mismatched, terminal, cancelled-predecessor, unresolved-effect, and no-contract cases abstained. This result says nothing about human effort, usefulness, anchoring, accuracy in real use, return-to-task correctness, GUI/model behavior, production safety, or product quality. No human study or real user data was used.

## Formal execution record

- Freeze commit: `e84a691d6a8fee0b3dfaa270f07dcfe1de84c00d`
- Branch base: `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`
- Allocation: `T0-A02`, separate from consumed `T0-A01`
- Runtime: Python `3.12.13`, Darwin
- Candidate: one invocation, exit 0; output `results/candidate_raw.json`
- Auditor: one invocation, exit 0; output `results/audit.json`
- Input SHA-256: `a16d8ad1c88811b11a309cbaf2925ec20442f525a25a7b1babb42b9ac06b755a`
- Candidate output SHA-256: `a6d4e8437579bd30ab1dfad4d8416004046e8e44ea26aed3ae996cd042a416df`
- Reconstruction: 12 cases, 0 errors
- Mutation gate: 6/6 rejected, each with an explicit reason in `results/audit.json`

Candidate/auditor stdout, stderr, exit records, original inputs, source, freeze manifest, and SHA-256 list are retained alongside the outputs. Construction tests passed 2/2 under normal Python and 2/2 under `python -O`. The strict analysis index passed before formal execution; rerun it after adding result artifacts and verify the final hashes before publication.

## Caveats

The mutations are six preregistered representatives, not an exhaustive adversarial search. The same auditor reconstruction function validates the baseline and mutated outputs, so common-mode defects in that validator remain possible. The independent topological-order reconstruction is distinct from the candidate's ready-frontier algorithm, but this synthetic exercise is method evidence only.
