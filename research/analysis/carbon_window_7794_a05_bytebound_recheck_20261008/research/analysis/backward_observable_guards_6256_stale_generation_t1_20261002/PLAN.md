# #6277 audit-only T1 — stale-generation mutation coverage

## H / T / D / C / U

**H.** An independent raw-only checker reproduces the frozen T0 preimage and its original mutation counterexamples, and shows that deleting `generation_fresh` admits a stale-generation state whose outcome is wrong-target/forbidden.

**T.** Allocation `BACKWARD-OBSERVABLE-GUARDS-6256-T1-AUDIT-20261002-01`. Candidate/runtime invocations 0; one independent audit; retries 0. Read only the three copied, byte-pinned T0 inputs under `inputs/`; recompute the total-correctness preimage, previous audit receipts and five existing mutation checks; add the explicit drop-generation mutation. No live process, GUI, model, network, user file, external action, or OS input. Host CPU only; Docker is not required for this local byte/hash audit.

**D.** Pass only when all three input SHA-256 identities and row counts match, the independent preimage matches T0 candidate output, all existing mutation counterexamples are independently reproduced, and the generation-deletion mutant admits `stale_generation` while the exact guard refuses it. Otherwise retain FAIL/HOLD without modifying or rerunning T0.

**C.** This is an audit supplement to an authored finite model. It does not validate transition-model completeness or real application behavior.

**U.** No live GUI safety, task effect, authority, model performance, latency/efficiency, or product claim.

## Pre-execution record

- Successor issue: #6277.
- Parent T0 artifacts: PR #6276 head `db8737f900627d7b2e185dd519363d4f86c5fcea`.
- Current main at this successor freeze: `5d16264201f0d8ea946bc507970fde872f280d95`.
- Candidate/runtime invocations: 0; audit invocations: 0; retries: 0.
- Construction-only unit tests will run before freeze; they use a toy model, not the frozen parent inputs.
