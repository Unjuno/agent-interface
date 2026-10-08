# Rescue of #6915 owned Linux pipe completion evidence

Original head `b0a4ada9bd41e74d4e6ea059c483ccb672cf917e`, PR #6915,
Issue #6501. Preserve all 53 original packet files. The original frozen OrbStack
Linux/aarch64 six-row candidate/auditor 1/1 allocation with zero retries remains
consumed; do not rerun candidate.py, driver.py or launch_once.py.

`python -B runtime/results/owned_pipe_rescue_6915/test_archive.py -v`
checks complete52-entry manifest, all15 frozen source/input pins and all seven
guest tar members byte-for-byte against retained extracts/readback identities.
No tar extraction occurs. It audits all six rows/127 events on fresh temporary
receipts, and regenerates all sixteen directed copied-raw controls on fresh
temporary outputs. Receipt JSON, control JSONL bytes and diagnostics must equal
historical evidence exactly, both normally and under `-O`. The raw-only auditor
imports no producer; explicit exception gates remain active under optimization.

The original result separates cancelled asyncio wrappers from unfinished running
concurrent Futures; closing the blocked read FD does not prove the callable
finished. The separately owned selector/control channel acknowledges stop and
closes read resources before its checkpoint. Native-thread absence is evidenced
only after explicit executor join. Harness data release in the first two policies
is cleanup, not cancellation-policy success. These policies use different
resource sets and I/O strategies; no equivalent-workload performance claim.

This is retained-data validation, not new OS observation or container allocation.
No old guest, daemon, model, live GUI/input, producer, backend or another worker
resource is invoked. Historical proc syscall/wchan predicates are backend-specific;
no cross-platform cancellation, arbitrary I/O preemption, simultaneous data/control,
multiwaiter, latency, current-source authority or production adoption is established.
Public resource/address-free derivatives do not reconstruct private originals.
