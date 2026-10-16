# Issue #8914: budgeted failure discovery T0 A01

This package is an offline synthetic method test only. It does not run GUI, game, model/provider, WSLc, Docker, or shared-runtime operations.

The prospective conditions are in [PREREGISTRATION.md](PREREGISTRATION.md) and [freeze.json](freeze.json). Candidate input contains shallow data only; deep outcomes are created only after the source freeze. The candidate and independent raw-only auditor are separate programs and share no imported code.

## Frozen execution sequence

1. Commit the preregistration, candidate, runner, auditor, and mutation controls before generating deep outcomes.
2. Run `python3 -m py_compile candidate.py run_t0.py audit_raw.py mutation_controls.py` as syntax-only validation.
3. Run `python3 run_t0.py` once. Preserve `raw/shallow-input.json` and `raw/candidate-output.json` unchanged.
4. Run `python3 audit_raw.py` once, then run `python3 mutation_controls.py` on temporary copies. Do not rerun or tune the allocation.

The audit is method-scoped. Even a pass does not estimate live GUI risk, establish safety, or certify a task cell as safe. Raw outputs and exact commit will determine the result.
