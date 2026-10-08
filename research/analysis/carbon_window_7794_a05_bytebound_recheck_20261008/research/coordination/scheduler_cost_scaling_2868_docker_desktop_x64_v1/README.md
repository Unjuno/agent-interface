# Candidate-queue cost scaling — Docker Desktop x86_64

Issue #5025 is a separate Docker Desktop/linux/amd64 cost point for the
all-ready synthetic queue question in #5021. The #5021 OrbStack/linux/arm64
allocation and image are untouched; this result is not an ARM64 comparison.

## Frozen protocol

For each of five candidate-set sizes (8, 32, 128, 512, 2048), the schedule
contains 15 paired blocks and an explicit seeded order of three policies.
Candidate priority and deadline ties are common; `enqueue_seq` is unique and
is part of the stable key `(-priority, deadline, enqueue_seq, op_id)`. Every
candidate is declared ready, unexpired, and independent. The exact schedule
bytes are retained at `input/schedule.json`.

Each policy/block is a fresh sequential Python child process. Child startup,
JSON input decoding, process serialization, and parent wait are outside the
worker interval. Key-tuple construction, queue construction, and complete
drain are inside it. The worker emits its complete ordered ID trace plus
process-CPU and monotonic-wall nanoseconds. The raw-only auditor independently
recomputes each expected order, verifies all 225 worker identities and paired
traces, binds child output to duplicated timing/trace fields, computes median
within-block CPU ratios, and challenges five evidence mutations.

Policies: repeated `min()` plus removal; one stable tuple sort then front-drain;
and `heapify()` plus `heappop()`. This is a reference microbenchmark, not a
production scheduler or an end-to-end desktop evaluation.

## Decision rule

`PASS_HEAP_COST_CROSSOVER_SCOPED` requires all 225 records and exits, exact
oracle traces for every policy/block, zero independent audit errors, all five
corruption controls rejected, and median paired heap/scan and heap/sorted-list
process-CPU ratios <= 0.80 at both queue sizes 512 and 2048.

If integrity and semantics pass but either threshold misses, report
`FAIL_HEAP_COST_THRESHOLD_NOT_MET` without changing the threshold. Any trace
mismatch is `FAIL_SELECTION_SEMANTICS`. Source/image/platform/denominator/audit
failure is `STOP_PROVENANCE_ENVIRONMENT_OR_AUDIT`, with no timing interpretation.

## Reproduction

The sole formal run and the separate audit are Docker Desktop-only, offline,
read-only-root invocations against image
`sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
Use fresh output directories and the frozen source/schedule hashes in
`FREEZE.json`. Do not rerun either allocation.

## Scope

One deterministic all-ready queue family, five sizes, 15 paired blocks, one
Docker Desktop 28.5.1 linux/amd64 host, CPython 3.12.14. This makes no ARM64,
dependency/resource scheduling, cancellation/reprioritization, starvation,
parallel execution, task/token savings, production adoption, or broad
cross-platform claim. The result only informs whether a later scheduler
integration evaluation is warranted.
