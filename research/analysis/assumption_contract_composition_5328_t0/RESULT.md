# Result — assumption-aware contract composition T0

Allocation: `assumption-contract-composition-5328-t0-20260930-01`
Issue: [#5328](https://github.com/Unjuno/agent-interface/issues/5328)
Frozen source main: `a1d0d0290b8619902d34b13d9e536c4bde063f74`

## H/T/D/C/U outcome

**H — PASS, scoped.** The independent raw-only audit returned `PASS_READONLY` with no errors; all seven cases matched the literal oracle. The fully discharged compatible baseline composed to PASS. False backend stability, expired capability, missing assumption evidence, and stale verifier digest composed to UNKNOWN. Protocol mismatch and false component guarantee composed to STOP. The flat local-guarantee baseline passed six of seven cases; five of those were local-only passes correctly prevented from becoming a composite PASS.

No authority or external effect was emitted.

**T/C:** One deterministic host run, Python 3.14.5 / Darwin arm64 / stdlib. Runner and raw-only auditor each invoked once. No Docker/OrbStack CLI, model, network, GUI/input, or external effect.

**U:** Synthetic three-node contract semantics only. No proof about arbitrary implementations, empirical assumption calibration, real external systems, or task success. A composed PASS is only as sound as the declared model and assumption evidence.

Raw/audit hashes are in `SHA256SUMS`; freeze and limitations are in `FREEZE.json` and `PLAN.md`.

## Local CI

```sh
python3 -B -m pytest -q test_model.py  # 5 passed
python3 -B -m py_compile model.py oracle.py runner.py audit.py test_model.py
git diff --check
```
