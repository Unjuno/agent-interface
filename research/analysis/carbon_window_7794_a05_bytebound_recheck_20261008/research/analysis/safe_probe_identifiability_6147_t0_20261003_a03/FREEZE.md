# Freeze — AI-6147-T0-20261003-03

- Frozen: 2026-10-02 15:43:09 UTC (2026-10-03 00:43:09 JST)
- Repository/base: `Unjuno/agent-interface`, `main` / `b521912b9da1fa292f2e4fed1f1ae695c4a7658e`
- Allocation path: `research/analysis/safe_probe_identifiability_6147_t0_20261003_a03/`
- Candidate source SHA-256: `a1625d2689145504ceb5e7087ad8f64d50e6c563cdf947be9683ee3547d76cf9`
- Independent auditor source SHA-256: `d7b462921313f064e6fd2579846b99a9584c792a37f480431557cbdc3d3cfce5`
- Plan SHA-256: `fb7b705be683ab6bc27e44e071c94de90e2fb8b8e00df6c597cbf0857a929e87`
- Interpreter: `/opt/homebrew/bin/python3`, CPython 3.14.5; executable SHA-256 `2477b47fa3ae65b9574eb18a15edb364e96948eaa1875ad3f1c80d780efc9c12`; standard library only.
- Formal runtime: host CPU only; no OrbStack/Docker, model, GPU, GUI, network, or physical input. No shared resource was used.
- Pre-freeze construction checks: `py_compile` for candidate and auditor; in-memory generation of 3 fixtures and depth-2 tree spaces; all passed. These are not formal result evidence.
- Output collision check: `RAW.json` absent immediately before invocation.
- Formal commands, once each and in order: `python3 -I candidate.py`; if and only if exit 0, `python3 -I auditor.py RAW.json`.
- Retry/tuning: none authorized; preserve first outcome as PASS, FAIL, or STOP.

H/T/D/C/U are frozen in `PLAN.md`. No source edits after this freeze.
