# Local construction validation — 2026-09-28

Scope: **benchmark-instrument construction and fixed-seed regression only**. The private reference controller may read hidden world state, so its success is not Agent Interface performance evidence.

Environment: current ChatGPT Linux execution container, Python 3.13.5, GCC 14.2.0, X11 1.8.12, Xvfb available. Docker/Podman CLI was not available locally; actual Docker image build/run is delegated to repository CI.

## Fixed allocation

`FIXED_SUITE.json` freezes the construction/regression allocation:

- primary seed: `424242`;
- matrix seeds: `7, 19, 42, 314159, 424242`;
- difficulty levels: `0.0, 0.35, 0.65, 1.0`;
- mechanics throughput allocation: seed base `1000`, `1,000` episodes;
- render throughput allocation: `1,000` frames.

Formal model evaluation must **not** reuse this fixed public allocation as held-out evidence. It should allocate fresh hidden seeds after B0/Candidate freeze.

## Construction tests

Native build:

- `make clean all`: PASS with `-O3 -std=c11 -Wall -Wextra -Wpedantic`.
- `core_tests`: **6/6 PASS**:
  - premature watcher acknowledgement -> `premature_action`;
  - repeated acknowledgement of a resolved generation -> `stale_action`;
  - wrong camera-feed target -> `wrong_target`;
  - wrong terminal code -> `typing_error`;
  - assembly release outside tolerance -> `assembly_miss`;
  - difficulty-axis validation rejects invalid values/unknown axes.
- Python regression suite: **9/9 PASS**:
  - fixed-seed state/event/input hashes replay identically;
  - different seed changes state hash;
  - fixed seed × difficulty reference matrix passes;
  - individual axis overrides are retained in reports;
  - invalid overrides fail closed;
  - deterministic PPM snapshots are byte-identical;
  - mechanics and render benchmark modes execute;
  - the fixed-seed parameter sweep is byte-equivalent across reruns and exposes an expected deadline frontier.
- Xvfb GUI smoke: PASS for seed `424242`, difficulty `0.45`, reference-controller completion in `1,682` ticks, state hash `d45401b07d81e288`.

## Local throughput diagnostics

These numbers characterize the instrument on this one host, not controller capability:

- `1,000` fixed-seed reference episodes at difficulty `0.45`:
  - `1,000/1,000` PASS;
  - wall time `0.440806364 s`;
  - **2,268.570 episodes/s**;
  - aggregate hash `c9609c85a867b119`.
- `1,000` CPU software-rendered frames:
  - wall time `1.800306125 s`;
  - **555.461 frames/s** at `640×360`;
  - final frame hash `31e8b63223f6a62d`.

These are local diagnostics and should be rerun on any formal evaluation host.

## Fixed-seed frontier smoke

`sweep.py` can sweep one declared axis while holding the fixed suite constant. Example:

```bash
python3 sweep.py --axis episode_deadline_ticks --values 600,1200,2400,10800 --difficulty 0.45
```

Observed construction reference result on the fixed five-seed suite:

- `600 ticks`: `0/5` success (`episode_deadline` ×5);
- `1200 ticks`: `0/5` success;
- `2400 ticks`: `5/5` success;
- `10800 ticks`: `5/5` success.

This demonstrates the automated frontier machinery only. A private perfect/reference controller is not a model benchmark.

## Container gate

The repository workflow builds the provided multi-stage Docker image, then runs inside that image:

- native C fail-closed tests;
- Python fixed-seed regression tests;
- Xvfb GUI auto-reference smoke;
- fixed-seed mechanics benchmark;
- CPU render benchmark;
- parameter sweep smoke.

A container PASS establishes reproducibility of the benchmark instrument. It does not promote any Agent Interface candidate.
