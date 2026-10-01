# #6150 T0 preregistration

Status: method-only, deterministic CPU experiment; no participant, model, GUI, external service, or container.

## H / T / D / C / U

- **H:** Under the one frozen event fixture, bounded attention batches will preserve exact per-card decision authority and urgent release while producing a different simulated queue schedule from the simple policies. Any simulated service-time difference is a fixture property, not evidence about people.
- **T:** Run the frozen candidate once on `fixture.json`, producing one JSON result for IMMEDIATE, FIFO, EARLIEST_DEADLINE, and BOUNDED_BATCH. A separate auditor consumes only fixture/result JSON and independently reconstructs policy schedules and validates every review, cancellation, expiry, card-bound receipt, and effect attempt. Run five planted corruption controls: cross-card receipt, stale version, wrong target/effect, duplicate receipt, and deferred urgent release.
- **D:** `METHOD_PASS_SCOPED` only if independent schedule/card reconciliation passes for all four policies and all five corruptions are rejected. Any mismatch is retained as STOP/FAIL; no edits or reruns after freeze. No human-benefit, queue-quality, or production claim follows.
- **C:** A plain earliest-deadline queue may dominate; batching may merely delay cards. The deterministic oracle checks protocol wiring only.
- **U:** The service durations and scripted choices are synthetic; no human comprehension, consent, switching cost, actual approval accuracy, external validity, or causal benefit is measured.

## Frozen event contract

Five decision versions: A accept, B deny, C-v1 canceled at t=2 and replaced by C-v2 at t=3, D no-response with deadline, and E accept. A hard urgent release R0 arrives at t=2 and must bypass the deferrable decision queue at t=2..3. Each accepted effect attempt must cite exactly its own card ID/version/principal/target/effect. No global or inherited approval exists.

Candidate, independent auditor, fixture and tests are frozen as source. Candidate and formal raw output paths are new and must be absent before each stage. Construction tests are not formal evidence. Formal sequence is exactly one candidate invocation followed by exactly one separate CPU auditor invocation; if the candidate exits nonzero or raw output is malformed, stop with no auditor or retry. No seed is applicable (deterministic finite event fixture).

## Resource boundary

Host CPU only, Python standard library, one process at a time. No GPU/CUDA, Docker/WSL, network experiment, model, GUI input, or shared container resource. Outputs are confined to the unique task-local scratch directory and are not part of the repository worktree.

