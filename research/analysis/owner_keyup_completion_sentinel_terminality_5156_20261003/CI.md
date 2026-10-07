# Local validation

Environment: macOS host, Python 3.14.5. The sparse-checkout retained-result index command exited 0 while warning that absent sibling directories were omitted. The repository's pull-request workflow checks the index against a complete checkout.

- Python AST parse and FREEZE.json parse: PASS.
- Zero-target-invocation source/fixture preflight: PASS; 25-row control/treatment shapes, exact source identities, and Python version verified.
- Frozen target synthetic CLI: 2 invocations, both exit 0; control and treatment both returned PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY.
- Independent raw-only audit: exit 0, no errors; FINDING_NONTERMINAL_COMPLETION_ACCEPTED.
- Artifact regression tests: 4/4 passed.
- Delivery-rebase regression tests: 2/2 passed. A temporary Git repository confirmed that preflight accepts a later delivery commit only when it descends from the frozen commit and retains all frozen dependency blobs; a changed dependency is rejected. Candidate invocations: 0.
- The frozen source commit remains `f474970f82d68b6648aac64f99048ad0c2fd5732`; it is an ancestor of the rebased checkout, and all four dependency blobs still match. The original formal-01 raw and audit outputs were not rewritten.
- Existing sparse-checkout CI dependency test: 1/1 passed after its source file was added to this local sparse selection. Its first module-name invocation failed during import because the file was not selected; no test method ran in that attempt.
- Sparse analysis-index check: exit 0; absent siblings were not treated as removals, so only the PR's full-checkout index result is authoritative.
- Formal X11 candidate/auditor, Docker, GUI/input, model, GPU, and application-effect tests: not run.
- The first shell redirection attempt failed before Python launched because its output directory did not exist; the setup failure and subsequent successful preflight are preserved.
- The first SHA256SUMS verification was launched from the repository root, so package-relative names did not resolve. It performed no writes; the manifest must be checked again from this package directory.
