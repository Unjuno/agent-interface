# Issue #4608 pre-registration

Successor to #4451. Preserve the predecessor freeze and unused formal allocation unchanged.

## H

On the locally pinned Linux/amd64 CPython 3.13.5 image, replacing only the two SHA-256 bytes-slice inputs with `memoryview` slices preserves the passive reader's receipts, cursors, and refusals while reducing traced Python peak allocations for long consumed prefixes without exceeding the timing guardrails.

## T

- Baseline is the current-main reader blob `3b4ac9af076bdc5dee94e09cbab22b17bc45173a`, verified at main `75b3d1e9cf1518ed7912670ea541fe969b2fb0cd`.
- Local image: `python:3.13.5-slim-bookworm`, image ID `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`; record actual platform/toolchain details and make no equivalence claim to #4451's earlier build.
- Use the same deterministic 1,048,576-byte / 4096-record corpus, cursors 0/2048/4064/4096, `max_records=32`, 3 fresh-process repetitions per arm/cursor, and the same contract block.
- Run locally in the pinned cached image, network disabled, read-only source and bounded resources. This is a CPU allocation microbenchmark; no GPU training is relevant.
- Every worker start/completion and captured output is durably journaled before proceeding. A supervised timeout/interruption must retain the corpus identity, completed rows, active worker identity and typed STOP. Construction injects a worker timeout and verifies the journal/STOP without formal rows.
- Freeze every input/source/image/gate hash before exactly one formal invocation; no retry, exclusion, seed/data replacement, or post-result tuning.

## D

Scoped PASS requires exact receipt/exception/cursor parity, fail-closed controls, all 24 resource workers plus both contract workers, candidate peak lower in all 3 matches at both cursors 2048 and 4064, median candidate/baseline peak ratio <=0.75 at both, wall and CPU median ratios <=1.20, independent raw-only audit `errors=[]`, and >=10 effective corruption rejections. Correctness mismatch is FAIL; correct but insufficient resource benefit is HOLD; incomplete or interrupted evidence is typed STOP/HOLD. Timeout consumes the allocation.

## C

No network/pull/install, external workflow, provider, user data, GUI/input, shared-reader modification, runtime authority, or product claim. Only local Docker Desktop with cached image ID, `--network none`, read-only source, dedicated output, and bounded CPU/memory/PIDs.

## U

Synthetic trusted fixed-width JSONL on one Linux/CPython/OpenSSL build with three technical repetitions. `tracemalloc` excludes native allocations; no RSS, physical I/O, concurrency, other-platform, end-to-end, task-effect, or production adoption result.
