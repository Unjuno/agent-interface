# Freeze — AI-6147-T0-20261003-04

- Frozen: 2026-10-02 16:01:14 UTC (2026-10-03 01:01:14 JST)
- Repository/base: `Unjuno/agent-interface`, `main` / `43f7cd88d91af05036fae2100ec4e155c59e105c`
- Allocation path: `research/analysis/safe_probe_identifiability_6147_t0_20261003_a04/`
- Candidate source SHA-256: `6d7954e92db969c566d41489a0c2f898f56bef1aecb28677e59ca78625f5f687`
- Independent auditor source SHA-256: `894b8f6f3da445952badccf51754efb3e442655022898e8b795163b47959274b`
- Plan SHA-256: `84c905277967894f212243a0ea8fedf5337b8c24b50e0b45546314957adc1464`
- Interpreter: `/opt/homebrew/bin/python3`, CPython 3.14.5; executable SHA-256 `2477b47fa3ae65b9574eb18a15edb364e96948eaa1875ad3f1c80d780efc9c12`; standard library only.
- Formal runtime: host CPU only; no OrbStack/Docker, model, GPU, GUI, network, or physical input. No shared resource was used.
- Pre-freeze construction: candidate/auditor syntax compile; independent fixture table parity; in-memory comparison of all 12 tree layers; terminal stale-action/convergence checks; injected unsafe-policy rejection. All passed; none is a formal outcome.
- Output collision gate: `RAW.json` absent immediately before invocation.
- Formal commands, exactly once each and in order: `python3 -I candidate.py`; only if exit 0, `python3 -I auditor.py RAW.json`.
- Retries/tuning: none authorized; preserve first outcome as PASS, FAIL, or STOP.

H/T/D/C/U are frozen in `PLAN.md`. No candidate/auditor/fixture source edits after freeze.
