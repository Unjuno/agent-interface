# Issue #5730 bounded construction preregistration

## Objective and scope

Test the concrete protocol failure retained by #59 allocation `MAP01-ROI-BREAK-EVEN-59-GPU-20261001-01`: a non-terminating null-output preflight error allowed a candidate to run, and truncated tool output left no complete raw artifact. This is the separately scoped CPU-only construction study requested by Issue #5730. It does not repeat, repair, or reinterpret the predecessor allocation.

## H / T / D / C / U

- **H:** A fail-closed wrapper can prevent candidate invocation on failed inventory, active-process, source-hash, and output-path gates; retain candidate stdout/stderr directly to files; and permit independent audit only for a zero-exit, complete, byte-hash-matching artifact.
- **T:** Freeze the exact main SHA and SHA-256 of this preregistration plus all Python sources. Run a 14-case stdlib unittest construction matrix, then exactly one fresh synthetic child candidate through the wrapper and one separate stdlib-only raw auditor. Cases cover empty/null inventory, active/malformed/failed inventory, changed/missing source, nonzero candidate, absent/truncated raw, output-path collision, post-publication raw mutation, happy path, and real child-process stdout/stderr capture.
- **D:** Each failed start gate asserts candidate invocation count 0. Candidate nonzero/missing/malformed output never reaches the auditor or scientific evaluation and has `scientific_result=NOT_EVALUATED` with null published raw digest. A valid synthetic raw must be durably captured, have a byte-derived SHA-256, and pass the separate raw-only auditor. Any post-write byte mutation must fail the raw digest check. The only allowed construction disposition is `PASS_CONSTRUCTION_ONLY`; no scientific GPU result is possible in this protocol.
- **C:** Windows 11 host, CPython 3.11.9, standard library only; deterministic synthetic inputs/process. No CUDA tensor, model, training, GPU benchmark, Docker/OrbStack, GUI, game, input, network, or external side effect.
- **U:** This does not qualify actual NVIDIA inventory command semantics under contention, atomicity under power loss, CUDA correctness/performance, model behavior, or #59 live threat-control acceptance. No GPU or container lease is requested.

## Frozen commands and paths

Construction suite (development plus mutation controls):

`python -B -m unittest -v test_fail_closed.py`

Single synthetic publication candidate plus conditional separate auditor:

`python -B run_construction.py --freeze FREEZE.json --output evidence/formal-01`

The output path must not exist before the second command. No retry is permitted. The child candidate output is redirected directly to files; it is never captured through the Codex tool response.

## Predeclared interpretation

Any failing assertion, frozen-source mismatch, nonzero candidate, absent/truncated raw, digest mismatch, auditor failure, or output collision is retained as a typed STOP/FAIL with scientific result `NOT_EVALUATED`. A construction PASS closes only this bounded protocol hypothesis and does not authorize any later GPU allocation.
