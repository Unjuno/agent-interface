# Host thread-overlap boundary result — 2026-09-28

## H/T/D/C/U

- **H:** on this Windows host, two Python threads can record one newly arrived
  feedback event and one trainer interval strictly overlapping an individual
  active call interval.
- **T:** one run of
  `python -B host_thread_overlap_probe.py thread_boundary_raw.json`; then one
  independent raw-only audit with
  `python -B audit_thread_overlap.py thread_boundary_raw.json thread_boundary_audit.json`.
  Source/gates were frozen in `BOUNDARY_FREEZE.json` before running. No seed,
  model, optimizer, GPU, Docker, or shared lane was touched.
- **D:** probe exit 0; two worker IDs distinct. Query-call interval:
  `[27524730411300, 27524730762900] ns`. Trainer critical section:
  `[27524730706500, 27524730967100] ns`. Their strict intersection is
  `56,400 ns` (56.4 μs). Feedback arrived at `27524730706200 ns`, after the call
  began and before it ended; consumption was at trainer start. Independent audit
  returned `PASS_HOST_THREAD_OVERLAP_INSTRUMENTATION_SCOPED`, zero errors.
- **C:** `thread_boundary_raw.json` SHA-256
  `f3c7582bda84279a48821b91c5e8d4386239cc291c4ef2ea41890612092ca611`;
  `thread_boundary_audit.json` SHA-256
  `53ae516627838f529ab55abbf07571acf282d82a7c4be580d8baa500076f99c7`.
  Python 3.11.9, Windows 10 build 10.0.26200, `perf_counter_ns` clock.
- **U:** the query is a barrier-blocked placeholder and the trainer interval is
  empty; no model or optimizer work occurred. This verifies only host thread
  event ordering/capture and does not establish Torch/GIL overlap, LoRA update
  concurrency, query quality, latency guarantees, or any #5081 formal threshold.

## Reproducibility boundary

The probe is one-shot and refuses to overwrite raw output. The independent
auditor uses only the standard library and independently checks cardinality,
clock ordering, worker distinctness, and strict call/update interval
intersection. Its zero-error result is scoped to this captured event record.
