# Phase-guided contiguous tile serialization — separate prospective allocation

Allocation `o2-contiguous-tile-copy-20260922-01`. Same research delivery namespace,
new subdirectory; no parent/profile freeze, input or result is changed. This is
a new mechanism/CPU experiment, not a retry of a timing or cleanup gate.

## Why this exact factor

The now-completed parent profiling allocation found median compression share
0.720997856 across12 changed conditions, but dense repaint conditions spent
0.5409–0.5502 of total profiled wall time copying/joining tiles. All12 observer
ratio gates and the raw reconstruction passed. This measured residual motivates
changing just `tile.tobytes()` to `np.ascontiguousarray(tile).tobytes()`.
The immediate comparator is the frozen vector encoder, not the profiler.
The canonical main encoder is retained as a third arm. CANDIDATE.diff shows
exactly the class rename and one serialization expression; no other algorithm,
compression, metadata, packet choice, evidence or authority change.

This choice is informed by the already viewed parent profile. The image corpus
is development-known, not held-out; fresh timings are collected. No parent timing
sample enters this allocation's metrics. The previous Intel result remains
unchanged; this AMD within-machine study cannot rewrite that result.
Targeted open/closed Issue search for ascontiguousarray returned no match.
No shared runtime files are changed, and no new Issue has actually been posted.

## H

Contiguous materialization reduces the costly strided-tile serialization path:
for each of3 dense repaint conditions, median paired candidate/vector update
wall-time ratio <=0.85, and the median of those3 medians <=0.80. Each of9 other
changed conditions must have median ratio <=1.10. Every initial/update packet
must remain byte-identical to both frozen comparators and the independent
pixel-row oracle. Unchanged conditions are retained diagnostics, not a benefit
claim. This is scoped encoding performance, never model or task performance.

## T

Use exactly the15 retained RGB image pairs, metadata, tile edge64, zlib level1
and fresh per-arm encoder priming described in the parent PLAN. Three arms:
legacy, vector, contiguous. Per condition3 warmup and21 timed triples, six fixed
rotating orders;315 timed triples /945 updates,45 warmup triples /135 updates,
1080 initial encodes outside timing. Total2160 encodes. Exactly three fixed
five-condition batches, each invoked once via synchronous execute.py with30s
child limit; failed/consumed batch stops, no retries or new samples.

Eight small synthetic construction methods passed before freeze: individual
channels/L/RGB/RGBA, unchanged/dense, partial/large tiles, modes, resizing/O1.
The formal source, corpus, auditor, environment and this plan are hash-frozen
locally and committed before timing. Remote write actions are not available,
so this is not public preregistration. No host/GUI/model/input/network work.

Actual environment: supplied Linux x86_64 container; AMD EPYC9V74 guest report,
affinity[1], clock not fixed; CPython3.13.5/NumPy2.3.5/zlib1.3.1 (built-in Python
zlib origin). BLAS/OMP thread environment1; batch one frame. See binary hashes
in ENVIRONMENT.json; no Docker/OrbStack/image-attestation claim. Captured frames
are frozen historical observations, never current action authority.

## D

PASS_CONTIGUOUS_TILE_COPY_SCOPED only if all15/315/45 denominators, all3 actual
external exit0 receipts, all packet bytes and raw-frame reconstructions, all
source/environment bindings and8 semantic mutation controls pass, AND all dense
and non-dense thresholds in H pass. Complete valid run missing performance gates
=> HOLD_TILE_COPY_BENEFIT_NOT_ESTABLISHED; byte mismatch=>FAIL_CODEC_EQUIVALENCE;
missing/source/process evidence=>STOP/HOLD. No reclassification or formal retry.
A PASS qualifies only this proposed implementation for further review, not
main promotion, general performance, unseen tasks or product acceptance.

## C

A contiguous copy introduces allocation and a second copy to Python bytes;
it can lose on already contiguous/tiny tiles or under memory pressure. The
fixed other-changed gates constrain regressions on this corpus. CPU/cache/
allocator/library implementation explain speed, not a semantic theorem.
No claim that copying is universally faster or that compressing the unchosen
full frame can safely be omitted. No scalar-confidence or lossy shortcut.

## U

Same development-known corpus, one execution environment, technical repetitions.
No held-out GUI/domain, end-to-end latency, bandwidth reduction (wire is equal),
tokens, model quality or human-speed claim. All samples including extremes are
retained; medians/ranges are descriptive. u_c is not calibrated; k=N/A.
One temporary contiguous tile costs at most12,288 raw bytes for formal RGB64x64,
excluding array/object/allocator overhead and unchanged byte-string accumulation.
This is a dimensional payload bound, not measured RSS or peak-allocation proof.

## Variables

| Symbol | Meaning/definition | SI unit | Domain/assumption | Type |
|---|---|---|---|---|
| A | Source tile's indexed uint8 channel values |1|nonempty rank3 ordinary ndarray|tensor|
| C | np.ascontiguousarray(A), dtype unchanged |1|same shape/content, C-contiguous|tensor|
| h,w | Tile height and width |1|positive integers <=64 in formal|scalars|
| c | Channels per pixel |1|formal3; construction1,3,4|scalar|
| y,x,k | Row, column, channel indices |1|0<=y<h,0<=x<w,0<=k<c|scalars|
| b | Serialized row-major bytes |1 (octets)|length h*w*c|byte vector|
| t_new,t_vector | Measured encode wall durations |s|positive, same monotonic clock|scalars|
| R | t_new/t_vector |1|positive|scalar|

## Complete byte-equivalence argument

For these ordinary uint8 ndarrays, ascontiguousarray with no dtype argument
preserves the dimensions and every indexed value. Thus C[y,x,k]=A[y,x,k] for
every valid index, including right/bottom partial tiles. tobytes() defaults
to C order, enumerating row, column, then channel in the same lexicographic
order for both arrays. Their elements are1-byte unsigned integers, so each
emitted element byte is equal and there is no endian or floating-rounding
operation. Therefore A.tobytes()==C.tobytes() at every byte position.

Each tile header still has the same x/y/w/h fields. The tile list and concatenation
order are unchanged, hence the uncompressed tile payload is equal. Same metadata,
canonical header encoding and deterministic zlib inputs give identical full and
tile wire packets. The strict smaller-packet choice is unchanged; state commit
is unchanged. Identical initial states plus this equal one-step transition imply
identical whole-stream bytes by induction. Failure/allocation behavior may differ
under resource exhaustion; no such equivalence is asserted.

Dimension check: h,w,c count elements; uint8 contributes one byte per element,
so h*w*c is the tile payload in bytes. For64,64,3 the bound is12,288 bytes.
Duration ratios cancel seconds, and are not throughput or model-token ratios.

## Roadmap and stop

Parent profile complete -> smallest candidate and construction complete -> this
local source/gate freeze -> three fixed measurement batches -> independent raw
reconstruction/8 mutations -> exact-source combined evidence/patch -> external
review, held-out workload and production-entry revalidation before adoption.
No unrelated branch deletion; GitHub publication/main integration remain separate.

## Primary semantics

NumPy2.3 ascontiguousarray: https://numpy.org/doc/2.3/reference/generated/numpy.ascontiguousarray.html
NumPy2.3 tobytes: https://numpy.org/doc/2.3/reference/generated/numpy.ndarray.tobytes.html
The docs specify shape/content and C-order behavior; they do not promise speed.
