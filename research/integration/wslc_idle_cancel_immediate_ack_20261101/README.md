# Held-input cancellation with immediate acknowledgement

This is a follow-up to [the delayed-ack held-input study](../wslc_idle_rpc_overlap_held_cancel_20261101/),
using draft #10094 candidate `477d54be7cd4e78df1de9601f62617a67558aea5`.
The earlier experiment deliberately withheld the child acknowledgement for
1 s and recorded `cancel_unconfirmed`. This experiment sets that delay to 0 s.
Other important injected conditions remain: a delayed X request, blocked X
sync, a synthetic target, and an enabled lifecycle guard.

Each of two serial WSLc allocations first observed `a` held using an independent
X client. The control did not request idle; the overlap arm attempted idle
and was refused without reserving it. Both reported `cancel_requested`, but
also `cleanup_status=UNKNOWN`, `late_server_request_possible=true`, and
`release_confirmed=false`. Separate X readback found monitored keys up after
release and at the delayed-request horizon; the synthetic old and fresh task
oracles passed. Those observations do not upgrade the runtime cleanup status.
Each arm ran once: this is not a general reliability, timing, or MAP01 result.

Main at freeze was `2c2b7114532f5f1434ccc34fca8ef48223314a72`. `raw.zip`
preserves frozen source, conditions, reports, test output, retained synthetic
artifacts and auditor output; host-specific `private-command.json` and Python
bytecode are excluded and their originals remain local. `archive-manifest.json`
hashes each entry. Run `python audit.py` to verify the archive and independently
check the held-input, cancellation, release and task-oracle fields, then run
the original saved-report auditor. This cannot prove unrecorded events absent.
