# v6 clock/cancel cooperative T1 — auditor stopped

Issue [#6232](https://github.com/Unjuno/agent-interface/issues/6232), successor allocation to #6228/#59. Frozen base: `673763554192ae26636e07d5a48f03b3cd7fb044`.

## Disposition

**STOP_AUDITOR_ROOT_PATH.** The candidate invocation ran once, after the construction-only cancellation check passed. The independent auditor was invoked once and exited before loading/recomputing the raw trace because its repository-root calculation selected the parent directory outside the checkout. Per the preregistration's one-audit/no-retry rule, it was not rerun. The candidate raw trace is retained, but no independently audited scientific PASS or FAIL is claimed.

The candidate stdout indicates A and B reached the expected cancellation/lease branches. Correct unit conversion gives C's candidate-side `release_ns - timer_expired_ns` as 56,200 ns = **0.0562 ms**, not 56.2 ms; the candidate-side raw values therefore appear to fall within the preregistered 50 ms timer-relative limit. This correction is recorded transparently. It is not a validated decision: the auditor failed before reading the raw trace, so no independent arithmetic or gate verification occurred; the candidate values remain unverified output.

## Preregistration and frozen sources

H/T/D/C/U, allocation, base, source hashes, candidate hash and auditor hash were recorded on #6232 before the candidate invocation. Base source Git blobs were:

- v6 runner `10344582ffa2ce339bc48dd8d680512a71f4eddc`, SHA-256 `9790becf98104b3a956c73bee945266a8517e41c2396c1a8b29c924e14d26012`
- executor v10 `e0a31884307eeac405094a624e3a63222acc656f`, SHA-256 `e55f82e6f15c39914a4213873d39386205a792c98b54d0cf54be0812c69ecb2e`
- Lease `b9dac6bb4063928354733d79bf371909a288a3d1`, SHA-256 `e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f`
- candidate `run_experiment.py`, SHA-256 `9ec8093d901576747c8d309df129d65365327a1108211f4314ebc874f1b25a75`
- auditor `audit_trace.py`, SHA-256 `3a23985483feb76d863d9b653d7a83610499bcfdd236067d39795b2e0edb468c`

Construction-only command passed before freeze:

```powershell
python research/doom/map01_recovery_v6_clock_cancel_order_59_t1_20261002/run_experiment.py --construct-only
```

It exercised the actual frozen Executor/Lease Git objects and observed verified cooperative release 0.0452 ms after the cancellation request. This is a harness construction check, not one of the three candidate scenarios.

Candidate command (once):

```powershell
python research/doom/map01_recovery_v6_clock_cancel_order_59_t1_20261002/run_experiment.py
```

Auditor command (once, failed):

```powershell
python research/doom/map01_recovery_v6_clock_cancel_order_59_t1_20261002/audit_trace.py
```

Failure: `fatal: not a git repository`; `audit_trace.py` used `HERE.parents[3]` where the repository root required `HERE.parents[2]`. No candidate or auditor retries. Windows host CPU, Python 3.12.10. Docker Desktop service remained stopped and shared Docker slot #5074 had no explicit release; no container, game, GUI, model, GPU, network, or input was used.

## Candidate raw output excerpt

These are runner-emitted fields, not independent-audit results:

| Case | Timer expired ns | Clock return ns | Cancel requested ns | Cancel observed ns | Release ns | Terminal | Matched |
|---|---:|---:|---:|---:|---:|---|---|
| A clock-before-cancel | 108131750833800 | 108132150957000 | 108132150992500 | 108132151024600 | 108132151031400 | completed | true |
| B lease-before-cancel | 108132751977600 | 108134352495500 | 108134352504400 | null | 108133658821100 | expired | false |
| C cancel-before-clock | 108134953426000 | 108135353908700 | 108134953443200 | 108134953477600 | 108134953482200 | completed | true |

Full output and all executor receipts: `raw_trace.json`. The exact auditor source that failed is preserved unmodified as `audit_trace.py`. No MAP01/runtime effect claim follows.
