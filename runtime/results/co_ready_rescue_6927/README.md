# Rescue of #6927: co-ready cancellation decision evidence

Retain all 38 original files (37 manifest entries) byte-for-byte from
`6ad7cd2cf31480e615de80f4b2ffdba2665d6314`, branch
`research/6501-co-ready-01a0ff52-20261003`, original delivery PR #6927.
Packet: `research/concurrency/pipe_co_ready_6501_20261003_01a0ff52_5884`.
Complete original history is archived at annotated tag
`archive/recovered/pr6927-source-6ad7cd2-20261004` before ref retirement.

## Fresh local retained-data validation, 2026-10-04 JST

`python -B runtime/results/co_ready_rescue_6927/test_archive.py -v`
passes three tests on macOS CPython 3.14.5 and bundled CPython 3.12.14.
Checks cover every original Git blob, all manifest sizes/hashes, 12 prospective
source pins against published commit `7e757470d8ac95faf7a9282fafd05d7b1d03a961`,
freeze identity, original raw identity/size, producer/auditor and local-check
receipt stream hashes. The original unsupported `--strict` usage exit2 remains
between the historical public-navigation exit0 and corrected workspace exit0.
Original setup/edit diagnostics, source plan and result are not modified.

Normal and optimized Python run only the retained-data auditor on the full raw,
writing a new output exclusively in a private temporary directory. All 20 rows
reconcile exactly with original `run-01/audit.json`. Eight corruption witnesses
are independently reconstructed from the original raw with exact typed mutations,
then checked byte-for-byte and hash-for-hash against archived copied controls.
Their audit CLI refuses every copy with exit1, no success output, and the exact
historical diagnostic under both modes. No candidate, launcher, native selector,
pipe deck, consumed producer or primary allocation is repeated.

A separate truth-table pass inspects actual recorded ready/selected/primary-read
events and five closure checks per row. First-ready violates the explicit
cancellation-first contract in C001 and C006 (two of four co-ready cells);
control-priority violates it in zero of four. Data-only/control-only/empty rows
are preserved, including the four empty polls. Ready order equalling write order
is checked as a historical observation of this deck, not an OS guarantee.

## Scope and integration disposition

The original Python 3.12.13, macOS27.0.1 arm64 KqueueSelector construction is a
single serial decision point with already-written one-byte pipes and authored
registration/write order. The selected runtime pins do not cover full kernel or
dynamic-library closure. FD closure is recorded evidence, not fresh inspection
of the original process. No latency, concurrent cancellation, future arrival,
arbitrary-I/O preemption, executor/join, portable backend, GUI/task effect,
physical release, model/token saving or authority claim is established.
The useful result rejects first-ready simplification under this explicit
contract; it does not invent a new mechanism or authorize production adoption.
Related #6915 is now closed, not merged as that original PR; its independent
historical delivery is not reopened or replayed here. Runtime/portable adoption
remains HOLD and #6501 remains open. Old committee/content approvals are not
revived by rescue integration. No runtime, workflow or shared index is changed.
After normal rescue PR integration, exact main equality, remote tag readback and
fresh paginated head/base/ref/descendant checks, user-authorized cleanup may
supersede the old delivery PR and retire the unchanged old references.
