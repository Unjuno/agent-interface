# Issue #5811 relational session non-interference T0

`PLAN.md` preregisters H/T/D/C/U. `fixture.json` is a deterministic synthetic set of ten A-alone/A+B histories. `candidate.py` checks a relational A projection; `audit.py` independently reconstructs dependency classes from source-bound resource evidence and verifies the candidate result. Construction tests are explicitly non-formal and do not consume an allocation.

Formal finite-fixture outcome: see `REPORT.md` and the immutable evidence under `results/5811-RELATIONAL-NONINTERFERENCE-T0-20261001-01/`.

The frozen candidate and auditor run once each in separate, network-disabled Docker containers. Each allocation has an immutable identity and retains its first result, including gate/operational STOPs. Never retry an allocation or overwrite a previous result directory. Formal results are limited to this finite synthetic method and do not establish live GUI, instrumentation, or production isolation.

Construction tests:

```powershell
python -B -m unittest research.analysis.relational_noninterference_5811_t0_v1.test_t0 -v
```
