# Needle role-skill lifecycle under WSLc

This is a fresh runtime-specific replication of the open lifecycle question in Issue #5084, tracked by successor Issue #6410. The -01/-02 stale-main/source/preflight STOP records remain unchanged and unconsumed formal results are not inferred from their construction checks. This package tests the exact retained seed-3788 package under Microsoft's native WSLc runtime with a new allocation identity.

The paired arms compare per-request full JSON load/validation/selected-role construction against full load/validation/all-role construction once and reuse, including reuse initialization in lifetime cost. The frozen 1,000-request schedule runs in 15 alternating paired blocks. See `PREREGISTRATION.md` and `FREEZE.json` for H/T/D/C/U, identities, commands, gates, and exact limits.

This is not a cross-runtime benchmark. The WSLc image uses CPython 3.12.14 and must be interpreted on its own; no numerical comparison to the older, unexecuted OrbStack CPython 3.13.5 proposal is valid.

## T0 disposition

The one-shot candidate completed 15/15 paired blocks and retained 30,000 predictions, but the separate one-shot auditor exited 1 before producing an audit report: its raw-tensor oracle expected top-level `enc.0.weight`, while this fixture nests tensors under roles A/B/C. This is `STOP_METHOD_FAILURE`, not a lifecycle result. Candidate/auditor counts are consumed, retries are forbidden, and the untouched raw output plus exact logs are preserved in `formal-output/` and the root logs. See `RESULT.md` and `SHA256SUMS`.
