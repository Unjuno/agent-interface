# Execution record — Issue #4853

Image: needle-pilot05:local, sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e, Linux/amd64 CPU. Offline, read-only root and source, 1 CPU, 2 GiB RAM, 64 PIDs. Dedicated writable formal volume; auditor mounts it read-only.

Construction command and frozen formal command template are recorded in `../CONSTRUCTION_REPORT.md` and `../FREEZE.json`. Construction returned `CONSTRUCTION_PASS seed=7866401 prefix_exact=True sentinel_bytes=True corrupted_prefix_rejected=True optimizer_updates=0`.

Exactly one formal invocation of `source/paired.py` completed: `prefix_exact=true`, `A_B_exactly_unchanged=true`, `base_immutable=true`; 400 base and 120 B/C updates per C arm. Control C=0.908447265625, treatment C=0.959716796875, delta=+0.05126953125. No retry.

Independent invocation of `source/audit.py` over the formal volume returned `{"A_B_exact":true,"delta_C":0.05126953125,"disposition":"PASS_RAW_AUDIT","errors":[],"prefix_exact":true,"reconstructed_cells":6,"seed":7866401}`.

The local output volume remains the source of truth. Exported raw-file digests are pinned in `SHA256SUMS.txt`; all matched hashes computed from the volume in a separate offline, read-only Docker invocation.
