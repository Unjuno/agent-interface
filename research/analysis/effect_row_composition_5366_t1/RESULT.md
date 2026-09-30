# Result — compositional effect-row contract T1

Allocation: `effect-row-composition-5366-t1-20260930-01`
Issue: [#5366](https://github.com/Unjuno/agent-interface/issues/5366)
Frozen source main: `8265c1a19cbba7ab0f5316f27bdb59509269399d`

## H/T/D/C/U outcome

**H — PASS, scoped.** On the nine frozen manifests, argument-only admission admitted 9/9. Compositional effect checks admitted the four pure/in-contract cases; rejected the polymorphic network instantiation and nested write masked by a wrapper; kept native and remote unknowns as `EFFECT_UNKNOWN`; and exposed one false reject where a possible write branch was over-approximated although the observed branch was read-only. The independent raw audit returned `PASS_READONLY`, zero errors, and all rows matched the literal oracle. No effect was dispatched and no authority was minted.

**T/C:** One deterministic host replay, Python 3.14.5 / Darwin arm64 / stdlib. Runner and raw-only auditor invoked once each. No Docker/OrbStack CLI, network, model, GUI/input, or external operation.

**U:** The corpus supplies finite manifests; it does not validate an actual source analyzer or prove manifest completeness. No compiler soundness, non-interference, arbitrary native/remote code safety, or runtime benefit claim. The observed false reject demonstrates a real availability cost of conservative unions in this toy corpus, not a calibrated rate.

Raw/audit hashes are in `SHA256SUMS`; freeze and scope are in `FREEZE.json` and `PLAN.md`.

## Local CI

```sh
python3 -B -m pytest -q test_model.py  # 5 passed
python3 -B -m py_compile model.py oracle.py runner.py audit.py test_model.py
git diff --check
```
