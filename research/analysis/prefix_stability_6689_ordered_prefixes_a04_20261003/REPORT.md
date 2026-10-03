# A04 report — ordered prefix preservation

## Question and lineage

Issue [#6809](https://github.com/Unjuno/agent-interface/issues/6809) remains open because the earlier #6809/#6812 package classified five authored terminal snapshots but did not enumerate every ordered event prefix. This A04 is an additive successor that exercises that missing temporal dimension. #6689 T0, #6809 S03, PRs #6811/#6812, and their raw evidence remain untouched.

## H / T / D / C / U

- **H:** A source-derived, order-sensitive prefix evaluator will preserve every still-pending mandatory obligation after an early negative, permit a complete mandatory negative without waiting on an unrelated optional source, and refuse a positive until the declared generation frontier is sealed.
- **T:** Four outcome combinations for mandatory obligations A and B, each under all six permutations of `result_A`, `result_B`, and `generation_sealed`; four prefixes per trace; candidate once and independent raw-only auditor once in separate WSLc 3.0.1.0 containers. No retries.
- **D:** `PASS_METHOD_SCOPED` requires all 24 traces/96 prefixes once, exact independent reconstruction, pending obligations retained until vector completion, completed negatives permitted with optional work still open, positive finalization only after seal, exclusive class counts separate from derived metrics, and rejection of all six frozen corruption controls.
- **C:** Deterministic authored traces cannot establish completeness of a live verifier's event vocabulary, event delivery, or future-event semantics.
- **U:** This is not a live verifier/runtime, GUI/action-safety, model, latency, product, migration-speed, hard-memory-limit, or general OOM result.

## Method and first outcome

The finite input fixes two mandatory result events and one generation-seal event. For each of the four pass/fail assignments, the protocol enumerates every event order. The candidate emits the initial state and the state after each event. The independent auditor constructs its own outcome Cartesian product, recomputes the six event permutations, derives each prefix from the raw input, and checks the complete JSONL including the summary row.

The first formal result is `PASS_METHOD_SCOPED`: 24 traces, 96/96 prefixes reconstructed, zero audit errors, and all six mutations rejected. Counts are 66 unresolved, 24 final-negative, and 6 final-positive rows. In particular, an early failure plus a still-missing mandatory result remains unresolved even after generation is sealed; a complete failure may finalize while the unrelated optional source is open; and a complete all-pass vector remains unresolved until the generation seal arrives.

Construction checks passed 9/9 before the formal invocation. Candidate and auditor ran once each, in distinct disposable containers, with the pinned Python image, network disabled, one requested CPU, read-only package/input mounts, and separate writable outputs. The source/input hashes before and after both runs matched the final freeze. Raw JSONL, audit JSON, child stdout/stderr, invocation receipts, and the host-visible WSLc warnings are retained in this directory.

## Runtime caveat and operational note

Both WSLc invocations emitted `wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The 512M setting is requested configuration only; no effective cap, swap bound, or OOM prevention is claimed.

One immediate post-candidate readback command was initially pointed at the parent workspace rather than the nested Git checkout and returned PowerShell path errors. It was read-only and changed no inputs or outputs. The inspection was repeated from the correct checkout, where the raw output, receipt, row/trace counts, and frozen hashes verified; the candidate was not rerun. A later construction-test discovery command was also issued from repository root, failed before importing tests, and then passed 9/9 when repeated from this package directory. Neither event altered the frozen source or changed the one-shot formal counts.

## Interpretation

This result closes only the finite ordered-prefix method gate defined in A04. It is useful compatibility evidence that this workload can be executed and audited in WSLc without Docker Desktop. It does not show that WSLc is faster or uses less memory than Docker or native WSL, does not establish the correctness of a production verifier, and does not close #6809's broader claim beyond the exact finite model. No Docker support or workflow default should change on this evidence alone.
