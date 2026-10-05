# Explicit-up cancellation boundary A03

A01 and A02 are retained as construction harness STOPs. A03 changes only source closure and wrapper access: it includes the exact `lease.py` dependency and follows the actual v4/v3 owner wrapper shape (`owner._inner` is the v12 owner). Tested owner and wrapper source bytes remain identical to the prior freezes.

This single deterministic fake-Xlib probe forces cancellation after the owner's false pre-dequeue sample and queue removal but before explicit key-up handling. OrbStack's daemon failed preflight before candidate execution, so the one candidate runs under host Python and does not establish container portability.

## Reproduction

```sh
python3 candidate.py
python3 audit.py
```

Run once only; preserve a STOP. See `PLAN.md`, `FREEZE.json`, `ENVIRONMENT.json`, and the bundled exact source snapshot.
