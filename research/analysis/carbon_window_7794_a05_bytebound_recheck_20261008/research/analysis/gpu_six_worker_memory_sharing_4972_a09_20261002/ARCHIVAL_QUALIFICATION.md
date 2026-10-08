# A09b source archive qualification

Issue: [#6329](https://github.com/Unjuno/agent-interface/issues/6329)
Original branch: `research/gpu-six-worker-memory-sharing-4972-a09b-20261002`
Original source commit: `58d2fa9deabfe767ece30144d6478de5e3eeb656`
Original freeze: `FREEZE.json` (preserved byte-for-byte)

This is a source-recovery/archive PR, not an experiment result and not
authorization to run the allocation. The original files and their historical
`SHA256SUMS` are preserved unchanged. `ARCHIVAL_SOURCE_SHA256SUMS` records the
actual recovered bytes independently; the original manifest's `runner.py`
entry does not match the recovered `runner.py` (expected
`7b395daa5f3f30bcf8ad7c8ba81b77863170908b71446aff2aa43126d3b7a073`, actual
`9069ad312b373b834c4efd416d160ee494fd0276cc894bab9415dc43a04b0839`). The
freeze also names an old base/current-main snapshot and is not a current
execution freeze. Neither discrepancy is silently repaired here.

## H/T/D/C/U

- **H — Hypothesis:** six bounded independent PyTorch processes can share an
  RTX 3080 working set and produce independently auditable checksums. This
  archive does not test that hypothesis.
- **T — Treatment:** the historical preregistration specifies six spawned
  workers, 192 MiB int64 tensor per worker, 20 increments, allocator fraction
  0.05, and an exact pinned PyTorch image/runtime. No candidate was launched.
- **D — Decision:** historical PASS/FAIL thresholds remain in
  `PREREGISTRATION.md`; no scientific decision is available. Current archival
  disposition is `HOLD / STOP_WSLc_SOURCE_RUNTIME_ADMISSION_FAILURE`.
- **C — Controls:** the recorded WSL GPU visibility smoke was a visibility
  observation only, not the pinned Podman/crun/CDI container or workload. No
  candidate, auditor, CUDA workload, or retry was run (0/0/0/0).
- **U — Uncertainty:** the exact source/runtime was not admitted at the
  allocation gate; the historical freeze is stale, its runner hash mismatches,
  and resource authorization/window is not current. A separate WSLc-native
  allocation-10 construction archive is PR #6815 and must not be pooled with
  allocation 09.

No GPU/resource request, candidate, formal audit, or retry is authorized by
this archive. Issue #6329 remains open for a separately coordinated,
freshly frozen successor if still scientifically useful.
