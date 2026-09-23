# Matched offline delivery-path cost

`probe_delivery_cost.py` replays exactly the same 48 presentation records from
actual-assistant servo-recovery-02 through three paths: no ledger, ledger v2,
and bounded/minimal-reference ledger v3. Twenty blocks alternate off/v2/v3 and
v3/v2/off. All raw measurements and four source hashes are frozen in
`results/delivery-cost-01`. No GUI input is executed by this experiment.

Each path serializes output, opens/appends/closes the delivered file per item,
and flushes a regular-file sink. Ledger paths additionally copy/decorate output,
retain references and open/append/close a receipt file. Temporary files are on
the repository's Windows-mounted filesystem under WSL. There is no fsync,
terminal/model transport, lock contention, capture, source journaling, projection
or command admission in the timed region. This measures the selected output path,
not whole-runtime instrumentation or model latency.

| Metric per identical trace | Off | v2 | v3 |
|---|---:|---:|---:|
| Median elapsed ms | 404.296 | 556.912 | 486.430 |
| Median paired difference from off, ms | — | +89.079 | +78.078 |
| Receipt bytes | 0 | 30,537–30,633 | 10,193–10,289 |
| Retained records | 0 | 48 | 16 |

The median paired v3-minus-v2 difference is -20.508 ms, with range
-268.914 to +132.379 ms; v3 is faster in 12/20 blocks. Different aggregate medians
must not be subtracted and called a paired result. Filesystem/order noise is
substantial. Storage reduction is clear; stable end-to-end acceleration is unproven.
Compared with the prior microbenchmark, per-record file I/O clearly belongs in
future profiling rather than extrapolating tiny bookkeeping timings.

`delivery_ledger_v3.py` retains only sequence/image/capture/reuse references for
observation-bearing output, including terminal receipts. It evicts oldest records
beyond 128 references (configurable positive integer). All output receipts are
still written; raw source observations remain in the original journal. The cap
bounds record count, not arbitrary string sizes or on-disk retention. Evidence
referring to an evicted record is rejected, so this is a visible contract change.
The inherited missing-reference error does not distinguish eviction from an
unknown/unflushed ID; refine that before integrating into a public entrypoint.

Verification checks that every sink reconstructs the same original records after
removing only delivery_id, source inputs remain unchanged, eviction rejects an
old reference, and a newer observation reusing the same PNG remains referencable.
The experiment is development-known replay, not task success or token evaluation.
The candidate is not wired into interactive_v16 or promoted by this result.
Next test an integrated bounded ledger with explicit eviction status and compare
buffered receipt persistence under output stalls before default adoption.
