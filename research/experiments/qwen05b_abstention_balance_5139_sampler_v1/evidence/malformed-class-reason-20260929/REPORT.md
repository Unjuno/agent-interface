# Malformed semantic-reason auditor robustness

Date: 2026-09-29 (Asia/Tokyo)

## H / T / D / C / U

- **H — Hypothesis:** the independent class derivation must fail closed if `intent.op` is a valid string such as `yield` but `intent.reason` is a JSON array/object; malformed evidence must be rejected, not crash the audit process.
- **T — Test:** synthetic sentinels formal `830513921`, support `830513922`; changed `support_pool[0].intent` to `{"op":"yield","reason":[]}` and `heldout_pool[0].intent` to `{"op":"yield","reason":{"malformed":true}}`. Same canonical input was exercised before and after the guard. No model, GPU, CUDA, Docker, GUI, or formal allocation was used.
- **D — Data:** pre-fix run raised `TypeError: unhashable type: 'list'` during membership in the allowed-reason set. Post-fix audit returned `integrity_pass=false`, `raised=null`, and explicit support/heldout class mismatch errors. The canonical altered input SHA-256 is `c1599c47985bcefc9d2c53ae760abacae88f050cb4dc4606159f70c3eea1c801`; output is `result.json`. The initial launcher import-path STOP is preserved in `launcher-stop.json` and was resolved by rerunning the same script with `PYTHONPATH=.`.
- **C — Conclusion:** class derivation now type-checks the reason string before set membership, preventing a second malformed-JSON TypeError. A regression test covers list and object reason values in both support and heldout pools. Full suite: **30/30 passed**; `git diff --check` clean. The reproducer intentionally supplies no raw arms, so `missing_raw:*` errors are expected and unrelated; the intended class-mismatch rejections and absence of an exception establish this mutation result.
- **U — Limits / next step:** one host, one fixed mutation family, synthetic data only. This is not a complete parser/fuzz campaign, model-quality result, or GPU result. Preserve the malformed-op and class-relabel evidence independently. #5139 remains stopped before GPU/Docker pending exact #5085 assignment and remaining model/source gates.

## Reproduction

From this package directory:

```powershell
$env:PYTHONPATH='.'
python evidence/malformed-class-reason-20260929/reproduce.py
python -m unittest discover -s . -p 'test_*.py' -q
```
