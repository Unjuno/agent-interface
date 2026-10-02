# Freeze — AI-6147-T0-20261003-05

- Frozen: 2026-10-02 16:07:22 UTC (2026-10-03 01:07:22 JST)
- Repository/base: `Unjuno/agent-interface`, `main` / `43f7cd88d91af05036fae2100ec4e155c59e105c`
- Allocation path: `research/analysis/safe_probe_identifiability_6147_t0_20261003_a05/`
- Candidate source SHA-256: `afc6178b6d9a15e49b123a6608bfff282edd62628aa4e29785ee654d9104d82b`
- Independent auditor source SHA-256: `4cc6ed284f3f501ba7ca915f92c66fdca075d132752e022f0933215c46f5aef3`
- Plan SHA-256: `e63dfe2965fa47f16aff8bf6bfaec9ecdc14e562ca8edd3123e3dc9b86132138`
- Interpreter: `/opt/homebrew/bin/python3`, CPython 3.14.5; executable SHA-256 `2477b47fa3ae65b9574eb18a15edb364e96948eaa1875ad3f1c80d780efc9c12`; standard library only.
- Formal runtime: host CPU; no OrbStack/Docker, model, GPU, GUI, network, or physical input.
- Pre-freeze checks: both scripts syntax-compiled; independently encoded machine tables agreed; all depth-0..2 policy spaces matched in memory; unique p→q convergence, identical safe output traces, exact terminal effect and unsafe-injection rejection passed. Construction only, not formal outcomes.
- Collision check: RAW.json absent immediately before invocation.
- Formal commands, exactly once each and in order: `python3 -I candidate.py`; only if exit 0, `python3 -I auditor.py RAW.json`.
- No retry or tuning. H/T/D/C/U are frozen in `PLAN.md`; no code or fixture edits after freeze.
