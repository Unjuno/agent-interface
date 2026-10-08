# Issue #8493 T0 A01 — temporal-regime confirmation

This additive experiment tests whether the stationary pooled recurrence confirmation used by #8152 can mask a harmful within-instance time block. It retains #8152's finite trace grammar and exact target/competing fingerprints, but uses new seed ranges and a frozen six-case temporal schedule. It does not rerun or modify #8152.

The protocol and exact decision gates are in [`PROTOCOL.md`](PROTOCOL.md); the frozen schedule is [`fixture.json`](fixture.json). Formal outputs are retained under `results/`, with a one-shot record and checksums. The result is method evidence for this authored finite model only.

The formal execution is pinned to host CPython 3.12.13 on macOS because the available OrbStack Docker image store returned `operation not supported` during read-only image inspection. No image pull, daemon restart, container operation, or network access by the candidate/auditor is part of this allocation. This does not claim an OrbStack execution or container transfer.

Construction checks (not the one-shot formal candidate):

```sh
python3.12 -B -m unittest discover -s research/analysis/stochastic_trace_reducer_8493_t0_a01_20261009 -p 'test_*.py' -v
python3.12 -B research/analysis/stochastic_trace_reducer_8493_t0_a01_20261009/test_preflight.py
python3.12 -B research/analysis/stochastic_trace_reducer_8493_t0_a01_20261009/construction_probe.py
```

The last command generates the frozen rows in memory and immediately runs the independent reconstruction and six corruption controls. It writes no formal raw file and does not invoke either frozen CLI.

The committed freeze binds every source/input file. After it is committed and recorded on Issue #8493, run exactly once:

```sh
python3.12 -B research/analysis/stochastic_trace_reducer_8493_t0_a01_20261009/run_formal.py
```

`run_formal.py` checks the clean frozen worktree, current Python version, source hashes, empty results path, and exact base commit before invoking candidate then independent auditor once each. It never retries.
