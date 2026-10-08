# Issue #8609 T0 A01 — versioned semantic degradation

**Disposition: `PASS_METHOD_SCOPED`.** The frozen candidate and independent raw-only auditor each ran once and exited 0; retries were 0. The auditor independently reconstructed all 1,024 contract rows with `errors=[]` and rejected all 6/6 frozen corruptions.

On the authored matrix, the versioned selector retained at least one supported read-only operation in 320 rows, compared with 1 row for the all-or-nothing baseline (319 additional rows). Per-operation eligible rows were `read_raw` 256, `inspect_semantic` 128, `admit_reversible_action` 2, and `verify_effect_evidence` 128; counts overlap. The action-admission rows are contract classifications only: no action was dispatched and no task effect was asserted. The two admitted rows differ only by ordinary telemetry availability, which the frozen action contract does not require.

The independent audit found no candidate mismatch, authority inflation, claim overstatement, dropped pending-release identity, hidden source, or monotonicity violation. All 512 rows carrying a pending release retained `lease-01` and blocked new action admission. Modes were `FULL_V1` 1, `CONTROL_CAPABLE_V1` 1, `READ_ONLY_V1` 318, and `NO_SUPPORTED_MODE_V1` 704.

Construction tests passed 7/7 under standard and optimized Python. Source regeneration reproduced the frozen model hash. The candidate raw output is 611,691 bytes with SHA-256 `3d5d6b8d400bf6824ba934e9b1fa10afc7a20b4ea2c44d4bdbdb3d57fa877dbf`; the audit JSON is 175 bytes with SHA-256 `929c2aee366da055e9fd9c240ce413c915ac775b6e9b1640a9a2f07613436486`. Commands, times, exits, freeze identity and complete package hashes are in [RUN_RECORD.json](RUN_RECORD.json), [FREEZE.json](FREEZE.json), and [SHA256SUMS.txt](SHA256SUMS.txt).

This is finite evidence for an analyst-authored contract only. It does not establish that real interfaces expose independent services, that the mode selector is safe or useful in a deployed controller, that any GUI action or task effect succeeds, or that failures occur with these frequencies. It does not authorize runtime fallback or weaken existing freshness, authority, verification, or release gates. The candidate/auditor ran on host CPython 3.14.5; OrbStack container execution was unavailable at preflight and is not claimed.

The package manifest covers all 19 retained package files other than the manifest itself; independent readback found zero hash mismatches and zero unmanifested files.
