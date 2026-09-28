# Issue #5172 Stage-0 specification

This is a test contract, not executable code. Implement as additive, independently auditable tests.

1. Fixture is a tiny raw JSON document for one allocation, seed, and arm. It contains ordered `base_row_indices`, a complete expected digest map, source/input identity, and no model weights or predictions.
2. Expected schedule is independently rebuilt from the frozen deterministic schedule parameters. Auditor canonicalization is implemented locally and must not import the runner digest/canonical function.
3. Positive control: exact valid document accepted.
4. Negative controls, one mutation per fixture: missing schedule; extra digest key; reordered indices; duplicate index; changed one index while preserving digest; changed digest while preserving indices; duplicate JSON key; NaN/Infinity; wrong arm; wrong seed; wrong allocation; malformed identity/schema.
5. For every case, patch/instrument runner fit and optimizer-step entrypoints and assert call count remains zero. Auditor fixtures must not call `run_seed` or generate training results.
6. Validate that each arm's schedule is reconstructed independently. Never compare exact final weights between differently batched arms.
7. Test expected typed disposition: invalid evidence is rejected as audit-contract failure; a malformed source freeze/resource/seed gate is STOP; no case can emit scientific PASS.
8. Retain test source, exact commands, environment, exit code, raw stdout/stderr byte counts and SHA-256. Do not overwrite any earlier run directory.

A complete Stage-0 pass requires all controls above; host tests are construction evidence only. Docker portability is a distinct check and requires a current explicit shared-CPU assignment, fresh inventory, pinned image readback, network none, read-only source/root, and a unique output directory.