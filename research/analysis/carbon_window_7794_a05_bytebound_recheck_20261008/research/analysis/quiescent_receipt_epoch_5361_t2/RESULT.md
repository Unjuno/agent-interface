# Result — quiescence receipt epoch binding T2

Allocation: `quiescent-receipt-epoch-5361-t2-20260930-01`
Issue: [#5361](https://github.com/Unjuno/agent-interface/issues/5361)
Frozen source main: `b0190453a787102189429e4b8c32032cf60efd17`

## H/T/D/C/U outcome

**H — PASS, scoped.** Independent raw-only audit returned `PASS_READONLY`, no errors. All ten frozen cases matched the literal oracle. Only the complete exact receipt bundle allowed reclamation; too-old, too-new, missing-epoch, wrong-authority, missing-reader, changed-registry, and duplicate-ID variants all blocked it. A valid new-epoch action remained admissible with reclamation blocked, while a stale action was rejected even when reclamation was allowed.

No authority was minted and no external effect occurred. T1's incomplete receipt-epoch gate remains intact as a separate failure artifact; T2 is a successor, not a rewrite.

**T/C:** One deterministic host replay, Python 3.14.5 / Darwin arm64 / stdlib. Runner and independent audit each invoked once. No Docker/OrbStack CLI under the current coordinator hold; no network, model, GUI/input, or external effect.

**U:** Finite synthetic receipt/epoch protocol only. Receipt fields are not cryptographically authenticated. No concurrent reader scheduling, crash consistency, actual RCU conformance, or production safety claim.

Raw and audit hashes are in `SHA256SUMS`; source/gates are in `FREEZE.json`.

## Local CI

```sh
python3 -B -m pytest -q test_model.py  # 5 passed
python3 -B -m py_compile model.py oracle.py runner.py audit.py test_model.py
git diff --check
```
