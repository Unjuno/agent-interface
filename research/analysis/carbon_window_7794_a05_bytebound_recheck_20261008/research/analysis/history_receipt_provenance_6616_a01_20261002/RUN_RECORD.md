# A01 terminal record

Disposition: `STOP_CONTAINER_SOURCE_MOUNT_EMPTY`; this is an infrastructure/setup STOP, not a scientific result.

- Allocation `HISTORY-RECEIPT-PROVENANCE-6616-A01-20261002` was frozen at commit `9c4df6785` on base main `9a327d0511f02c7b8ebd175e20f96a43028578ca`.
- Construction tests passed 4/4; formal candidate invocation count 1 (container started, Python exited 2); auditor 0; retries 0.
- Container `6616-a01-candidate`, ID `fac43070b9f0`, exited 2, `OOMKilled=false`. Its log: `python: can't open file '/src/candidate.py': [Errno 2] No such file or directory`.
- `orbctl push` used destination `root/6616-a01/`, which is relative to root's home, while the bind mount expected `/root/6616-a01`; the expected mount directory contained only `out/` and no source files. The candidate did not read fixture data or emit a scientific raw result.
- No auditor was launched. The consumed A01 is not retried or repaired in place. A02, if run, has a distinct allocation ID and output namespace with a verified post-transfer file/hash gate.

This STOP says nothing about the lifecycle-classifier hypothesis. Preserve it as-is.
