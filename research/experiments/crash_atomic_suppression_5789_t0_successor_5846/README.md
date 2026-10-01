# Crash-atomic suppression persistence — Issue #5846 successor T0

This is a new, additive experiment succeeding the immutable Issue #5795 record.
The predecessor's one-shot formal invocation stopped at
`STOP_FORMAL_ARGV_MISMATCH` with candidate/auditor counts 0/0; it is preserved
without retry. This package tests only a finite single-process `SIGKILL` /
restart fixture, not power loss, multi-writer serialization, an application
runtime, physical database-file compaction, GUI effects, or product safety.

Issue #5846 is the successor intake. The dedicated branch is
`research/crash-atomic-suppression-5846-t0-20261001`, and the additive path is
`research/experiments/crash_atomic_suppression_5789_t0_successor_5846/`. At this
point the successor is construction-only; formal candidate and auditor counts
are 0/0. Its reserved, user-authorized Obstac slot is
`crash-atomic-suppression-5846-t0-20261001-01`, 07:35–08:05 UTC, coordinated in
Issue #5085. The new guest/context, main SHA, hashes, path mapping, and output
gates must all be rechecked at the start gate.

## Files

- `FREEZE.md`: H/T/D/C/U, frozen schedule and start-gate boundaries.
- `FREEZE.json`: executable hash/runtime manifest, frozen after source commit.
- `protocol.py`, `worker.py`, `runner.py`: cases and toy candidate arms.
- `audit.py`: raw-only auditor; imports none of the candidate/protocol code.
- `container_runner.py`: bounded candidate/auditor Docker invocations and gates.
- `CONSTRUCTION.md`: host-only rehearsals, failures, and predecessor STOP.
- `SHA256SUMS`: source/freeze-file hashes for local verification.
- Formal outputs are created only after the start gate at
  `results/5846-01/`; do not pre-create empty result directories.

## Local checks

From repository root:

```sh
python3 -B -m unittest discover -s research/experiments/crash_atomic_suppression_5789_t0_successor_5846 -p 'test_*.py' -v
python3 -B -m py_compile research/experiments/crash_atomic_suppression_5789_t0_successor_5846/*.py
git diff --check
python3 research/analysis/check_index.py
```

Host-only checks are construction evidence and never count as formal rows. The
candidate uses the pinned Python 3.12 slim Linux/arm64 image, one CPU, 256 MiB,
64 PIDs, no network, read-only root/source, and a dedicated output mount. The
auditor runs only after a zero candidate exit, in a separate container with
read-only source/raw input and a distinct output mount. Do not use shared
OrbStack context. Preserve every formal STOP/FAIL and never retry the allocation.
