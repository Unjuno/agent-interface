# Issue #7367 closed workflow contract A01

This package tests a narrow answer to the completeness gap from the previous counterexample: for a closed, declarative machine workflow, compile the graph from the exact manifest the restricted interpreter executes. The interpreter exposes only manifest-declared evidence fields and rejects dynamic operations, changed source, unknown successors, and undeclared dispatch before liveness can prune context.

See `REPORT.md` for scope and disposition. `manifest.json` is the frozen workflow source; `run_a01.py` is the candidate; `audit_a01.py` independently enumerates reachable uses and checks each fail-closed control. The package reuses the frozen A01 liveness function without modifying its source. No model or production runtime was exercised.

`SHA256SUMS.txt` hashes Git blob bytes, so checkout newline conversion on Windows does not change the evidence digests. Verify entries with `git cat-file blob HEAD:<path>`.
