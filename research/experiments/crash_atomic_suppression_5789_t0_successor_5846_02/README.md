# Crash-atomic suppression persistence — Issue #5846 allocation-02

This additive package succeeds allocation-01's terminal pre-candidate
`STOP_MAIN_ADVANCED_AT_FORMAL_START_GATE`; that STOP remains immutable at
`research/experiments/crash_atomic_suppression_5789_t0_successor_5846/results/5846-01/PREFLIGHT_STOP.md`
and PR #5896. Allocation-02 is a distinct fresh allocation, not a retry of the
consumed slot. Issue #5795's predecessor `STOP_FORMAL_ARGV_MISMATCH` also
remains unchanged. No scientific result exists until this package's candidate
and independent auditor have actually run.

Branch: `research/crash-atomic-suppression-5846-t0-20261001-02`.
Path: `research/experiments/crash_atomic_suppression_5789_t0_successor_5846_02/`.
Allocation: `crash-atomic-suppression-5846-t0-20261001-02`, reserved for
12:30–13:10 UTC in coordination Issue #5085. New isolated guest/context are
`crash-atomic-5846-20261001-02` / `crash-atomic-5846-local-02`.

## Files

- `FREEZE.md`: H/T/D/C/U, frozen schedule and start-gate boundaries.
- `FREEZE.json`: exact executable/runtime/output manifest, frozen after source commit.
- `protocol.py`, `worker.py`, `runner.py`: cases and toy candidate arms.
- `audit.py`: raw-only auditor; imports none of the candidate/protocol code.
- `container_runner.py`: bounded candidate/auditor Docker invocations and gates.
- `finalize_freeze.py`: bind the guest daemon's observed image ID, source
  commit, and exact host↔guest output mapping into the final pre-run manifest.
- `CONSTRUCTION.md`: host-only rehearsals and allocation-01 lineage/STOP.
- `SHA256SUMS`: source/freeze-file hashes for local verification.
- Formal outputs will be created only after a passing start gate at
  `results/5846-02/`; do not pre-create output directories.

## Local checks

From repository root:

```sh
python3 -B -m unittest discover -s research/experiments/crash_atomic_suppression_5789_t0_successor_5846_02 -p 'test_*.py' -v
python3 -B -m py_compile research/experiments/crash_atomic_suppression_5789_t0_successor_5846_02/*.py
git diff --check
python3 research/analysis/check_index.py
```

Host-only checks are construction evidence and never count as formal rows. The
candidate uses the pinned Python 3.12 slim Linux/arm64 image, one CPU, 256 MiB,
64 PIDs, no network, read-only root/source, and a dedicated output mount. The
registry index digest (`2f17fc…`), ARM64 platform manifest digest (`950206…`),
and image-config digest (`8630ab…`) are distinct identifiers. The final freeze
also records and verifies the actual guest daemon's `image inspect .Id` before
launch. The auditor runs only after a zero candidate exit, in a separate
container with read-only source/raw input and a distinct output mount.
Allocation-02 is one shot; preserve every formal STOP/FAIL and never retry it.
