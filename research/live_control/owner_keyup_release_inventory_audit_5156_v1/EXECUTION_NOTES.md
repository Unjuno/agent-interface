# Execution notes — Allocation 06

The frozen GitHub commit was refetched and all 13 file contents matched the precommit source strings; SHA-256 checks over those strings matched FREEZE.json.

The ephemeral local execution copy was generated through a patch operation that normalized mixed LF/CRLF endings in input_owner_v10.py and input_owner_v11.py. The resulting byte hashes did not match FREEZE.json. Python source semantics are unchanged by those line-ending transformations, and the exact GitHub blobs remain independently pinned, but the execution is not byte-identical to the frozen blob. Therefore this is reported as a scoped synthetic construction PASS with an explicit reproducibility limitation, not as a byte-identical confirmatory run.

A separate Python process ran audit_independent.audit over the saved RUN.json and expected inventory and returned errors=[].

No Docker/OrbStack shared lease, real X11, GUI, physical input, game, model, GPU, or MAP01 test was run. The original #5298 Allocation-03 remains unchanged. The prefreeze fixture-reference failure and the unsuccessful local byte-hash comparison are retained as non-scientific tooling issues, not silently overwritten.

Saved artifact SHA-256: RUN.json `c71ac6df8c53bd1b426326b77b1ddcdd57bffa3c729dd8310a6b5eab7c2c5b0e`; AUDIT.json `3a47c4399aab4b48b324625d4e78576af76ddd63451a21358dec6edb691e9897`.
