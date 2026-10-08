# Result — Docker Desktop x86_64 candidate-queue cost

## Disposition

**`FAIL_HEAP_COST_THRESHOLD_NOT_MET`** for the preregistered hypothesis in
Issue #5025. The semantic and provenance gates passed: all 225 worker records
completed, every policy emitted the exact same frozen key-oracle trace in every
paired block, the independent raw-only auditor reported zero errors, and all
five corruption controls were rejected. The heap did not meet the preregistered
20% CPU reduction against both comparators at queue sizes 512 and 2048 because
the sorted-list policy was faster than the heap at both sizes.

This is a valid threshold miss, not a STOP and not a selection-semantics failure.
No threshold or allocation was changed after observation. The raw outcome does
not establish a production scheduler choice.

## Results

Ratios are medians of within-block heap/comparator process-CPU ratios. CPU
medians are nanoseconds for one complete queue construction and drain.

| Queue size | Scan median CPU ns | Sorted-list median CPU ns | Heap median CPU ns | Heap / scan | Heap / sorted-list |
|---:|---:|---:|---:|---:|---:|
| 8 | 17,971 | 18,884 | 27,626 | 1.1995 | 1.0184 |
| 32 | 47,422 | 27,877 | 43,114 | 0.6702 | 1.2408 |
| 128 | 306,792 | 65,264 | 82,903 | 0.2496 | 1.1461 |
| 512 | 5,210,026 | 288,355 | 329,190 | 0.0684 | 1.2617 |
| 2048 | 78,927,133 | 2,688,266 | 2,878,195 | 0.0373 | 1.1247 |

The result separates the alternatives: the heap substantially beats repeated
linear minimum-scan for large queues, but the frozen sort-once/front-drain
implementation is faster than the heap at every measured size >=32, including
by about 26% at size 512 and 12% at size 2048 in median paired CPU ratio terms.
The scan is fastest at size 8. This does not price queue reprioritization,
eligibility changes, cancellations, resource checks, or real scheduling logic.

## Integrity and execution

- Docker Desktop Engine 28.5.1; context `desktop-linux`.
- Pinned image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64, CPython 3.12.14.
- Formal invocation: 1; retries: 0; worker rows: 225/225; runner exit: 0.
- Separate Docker raw-only audit exit: 0; status `PASS_AUDIT_AND_TRACES`; errors: `[]`; exact oracle traces: 225/225; corruption controls rejected: 5/5.
- Frozen schedule SHA-256: `f778860219a8a9ffe8014eb00eeb41456dac1bf58a2687ee64045a2b9e1df733`.
- Exact schedule JSON: 262,252 bytes; lossless gzip 21,953 bytes, SHA-256 `324e8690cad622efffd8a81bbcdc0ccf25944f8d3254e76a5774becb6998dcf8`.
- Raw JSON: 1,688,320 bytes, SHA-256 `d0284b83b4a4c2f5c8efe1c3a9411bd2c5fd99ca97e0e9761f9c6e820f328228`.
- Lossless gzip: 119,128 bytes, SHA-256 `091d382eb4f6102a5991791405d65be58a422abfaf04f2b0e1e8b7a075261b38`.

The gzip/Base64 fragments in `input/` and `formal/` are ordered by the
accompanying `RAW_ARCHIVE_MANIFEST.md`. After concatenation, Base64 decode, and
gzip decompression, the schedule and raw JSON must match their byte counts and
SHA values above.

## H/T/D/C/U

- **H:** The heap preserves the stable full order and reduces process CPU by at
  least 20% against both scan and sorted-list at 512 and 2048. The exact order
  held; the performance threshold failed against sorted-list at both large
  sizes.
- **T:** Five fixed sizes × 15 paired blocks × three policies; a fresh child
  process per policy/block; queue construction plus full drain timed with
  `process_time_ns`; one offline Docker Desktop formal invocation and one
  separate offline independent audit.
- **D:** Retain `FAIL_HEAP_COST_THRESHOLD_NOT_MET`; see medians/ratios above.
  All 225 complete traces equal the independently recomputed tuple oracle.
- **C:** Identical frozen candidates, key, randomized-within-block policy order,
  Python, image, CPU quota and timing clocks; only the selection data structure
  changed. Quota scheduling, interpreter overhead, and one synthetic
  all-eligible queue family limit the precision and transfer of absolute costs.
- **U:** One Docker Desktop linux/amd64 host, CPython 3.12.14, synthetic
  all-ready independent jobs. No ARM64 comparison, dynamic eligibility,
  cancellation/reprioritization, starvation, parallelism, runtime adoption,
  GUI, end-to-end latency, task/token savings, or production claim.
