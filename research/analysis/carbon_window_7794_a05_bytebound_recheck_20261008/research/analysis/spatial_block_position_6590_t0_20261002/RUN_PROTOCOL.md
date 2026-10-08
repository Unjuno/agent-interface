# Frozen Issue #6590 T0 protocol

Allocation: `spatial-block-position-6590-t0-20261002-01`
Scientific base: to be recorded in `FREEZE.json` before invocation.
Old allocations: none consumed for #6590. #4752/#4814 remain immutable historical evidence.

## Commands and cardinality

Construction only, before freeze:

```sh
python3 -B -m unittest discover -s research/analysis/spatial_block_position_6590_t0_20261002 -p 'test_*.py' -v
```

After freeze and source-hash verification, execute exactly once:

```sh
python3 -B research/analysis/spatial_block_position_6590_t0_20261002/candidate.py \
  --fixture research/analysis/spatial_block_position_6590_t0_20261002/fixture.json \
  --output research/analysis/spatial_block_position_6590_t0_20261002/results/raw.json
python3 -B research/analysis/spatial_block_position_6590_t0_20261002/auditor.py \
  --fixture research/analysis/spatial_block_position_6590_t0_20261002/fixture.json \
  --raw research/analysis/spatial_block_position_6590_t0_20261002/results/raw.json \
  --output research/analysis/spatial_block_position_6590_t0_20261002/results/AUDIT.json
```

Candidate count 1; independent auditor count 1 only if candidate exits 0; retries 0. Preserve stdout, stderr, exit status, start/end timestamps, Python/platform identity, and SHA-256 for fixture/source/raw/audit. Do not edit frozen source, fixture, decision gates, or prior evidence after candidate invocation. A nonzero candidate or auditor is a terminal T0 failure/hold; no repeat under this allocation.

## Environment boundary

This exact T0 is a finite, no-model method control and performs no fit. In this macOS execution task `wslc.exe`/`wslc` are not installed; the OrbStack daemon has another active task's `unjuno-native-ci-6092` container and no explicit release/assignment. Therefore this T0 is executed as two separate local host processes, without touching the shared container. This deviation must remain visible in the run record. It is not T1 evidence; T1 requires its own fresh WSLc-eligible CPU allocation and preregistration.

Network/API calls 0; GUI/effect/authority 0; GPU 0; model fits 0. Output is synthetic method evidence only.
