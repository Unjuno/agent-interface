# Issue #6274 T0 — preference-explicit choice method test

## Disposition

**PASS_METHOD_SCOPED.** A pinned Docker candidate and separately implemented raw-fixture auditor each ran once and exited 0; retries were 0. The auditor independently enumerated the five fixture cases, reconstructed all outputs, and rejected all four predeclared mutations. Exact outputs and invocation records are in results/formal-01/.

## Findings

- In the complete conflict case, all principals explicitly rank review above quick despite review's higher latency. Requester-fastest chooses quick; the certificate finds review strictly Pareto-dominates quick. The complete frontier is {conflict, review}; neither is selected automatically. The explicitly declared equal-weight Borda baseline selects review, only as a named ordinal comparison rule, not as a fairness or welfare result.
- The partial case has three valid completions for the requester's missing review/conflict comparison (either strict order or a tie). Its possible frontier is {conflict, quick, review}; its certain frontier is {conflict, quick}; review remains unresolved. The apparently top-ranked d_route is removed before comparison because collaborator_c's grant was revoked.
- In the protected case two of three principals rank quick first, but collaborator_b's nontradeable private-content constraint excludes quick before preference comparison. Removing that constraint is caught as a mutation.
- An explicitly delegated collaborator_c can select conflict from the eligible set. With all principals tied, all four options remain on the frontier and no automatic selection is made.
- Four invalid variants were rejected: grant-as-indifference, fabricated missing rank, override of a nontradeable constraint, and false uniqueness of a multi-option frontier.

## Scope

This is a finite synthetic method result, not a human preference or shared-workspace result. It does not establish fairness, welfare, consent, satisfaction, legal status, live safety, GUI correctness, or a production choice policy. Its conclusions are conditional on the stipulated identical requester effect, candidate set, grants, constraints, and ordinal comparisons. T1 remains separately gated.

## Reproduction and verification

The pre-run freeze binds source hashes and current main 389b109629ca0c8baf7a9daf725eded76c358162. The formal image is python:3.12-alpine@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b (linux/arm64); network none; 1 CPU; 512 MiB; 64 PIDs; read-only root; 16 MiB /tmp. Source/fixture mount read-only; only formal-01 output mount writable.

Construction tests pass 9/9. Applicable Analysis Index checks were also run locally: index check and both workflow unittest suites; results are recorded in RUN.json. No real people, model, GUI, network request, shared file, or real authorization was used.
