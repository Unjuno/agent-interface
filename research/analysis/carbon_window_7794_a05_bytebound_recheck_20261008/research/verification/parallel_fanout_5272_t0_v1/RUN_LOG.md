# Formal run log — allocation `parallel-fanout-5272-t0-20260930-03`

- Issue: #5272, open at preflight.
- Frozen main: `70b69b47845b35afde59c2a5f0b56c6f906c6904`.
- Preflight main: `57b56de2831204885c55375737580e5d82d3ab98`, descendant of the
  frozen main by six commits. GitHub compare showed changes only in the
  #5305/#5318 research paths and runtime CLI/result paths; none touched the
  frozen experiment or listed contract files.
- Exact frozen source commit on GitHub: `db87baa28fe64b2379aafebe227cc1d9f8c7e19e`.
- Host: Windows PowerShell, Python 3.12.10, standard library only. No model,
  GUI, network, external verifier, or input/effect was involved.
- Formal runner invocation count: **1**. Command: `python simulator.py` with
  `RAW_OUT=C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\.cache-memory-lab\5272-run\evidence\formal03\raw.json`.
  Collision check passed; exit code 0; 18 rows.
- Raw SHA-256: `5d2914f3eb1a2d2b9fd8fb1fbefd391a6832a136f024d43cb4d30dc4aa2fcddf`.
- Canonical frozen-workload digest in raw: `c20516cfb45952a8f2a60f7dac1966df7dea2e145cf79850339fb31af06d93cd`.
- Separate raw-only audit invocation count: **1**, only after runner exit 0.
  Command: `python audit.py` with `RAW_PATH` set to the exact raw file above.
  Exit code 0; error count 0; corruption controls rejected 6/6. Auditor
  implementation does not import the simulator.
- Construction tests immediately before formal: 9/9 passed. These are not
  counted as formal executions.
- Docker/OrbStack: not used. The shared execution-lane record requires a fresh
  exact allocation; this deterministic standard-library model has no
  container-specific dependency. No container-backed result is claimed.
- No retry, replacement, or post-result source edit occurred. The raw file is
  preserved at the listed local evidence path and is also published in this
  directory as `out/formal03/raw.json`.

The initial two preparation attempts are separate retained pre-formal STOPs:
PR #5331 (`-01`, stale base) and PR #5335 (`-02`, malformed freeze blob).
Neither invoked the runner; neither is scientific evidence for or against the
hypothesis.
