# Issue #7411 T0 A01 — synthetic worthwhile-benefit method check

## Disposition

`HOLD_AUDIT_INCOMPLETE`. The frozen candidate and auditor each exited 0, and the auditor printed `PASS_METHOD_SCOPED`. Post-run review found that the auditor did not implement the full preregistered raw-record and mutation validation gate, so that nominal pass is not accepted. The candidate produced a useful provisional synthetic estimator result, but the formal method gate remains unverified.

## Question and frozen gate

The Issue asks how a future matched, correctness-gated route comparison might anchor “worthwhile” speed gains to users. The T0 question was narrower: can an estimator recover planted heterogeneous minimum-worthwhile-saving medians from synthetic paired-choice data, abstain when dose support is insufficient, and keep preference subordinate to a hard correctness gate? The exact H/T/D/C/U, generator, estimator, criteria, and limits were frozen in [PROTOCOL.md](PROTOCOL.md) before formal execution.

## Result

The candidate emitted 4,160 response rows over 160 simulated respondents, 13 savings doses, and two timing locations, plus 80 low-support rows. Its monotone pooled-binomial estimator returned:

| Timing location | Frozen synthetic median | Estimate | Absolute error | Gate |
| --- | ---: | ---: | ---: | --- |
| Planner-boundary wait | 10 s | 9 s | 1 s | Pass (≤2 s) |
| Local processing | 14 s | 13 s | 1 s | Pass (≤2 s) |
| Low-support control | Not identified | `UNKNOWN` | — | Pass |

The frozen auditor recomputed both estimates from the raw ledger, checked cross-location dose pairing, returned `UNKNOWN` on the low-support control, and confirmed that the correctness-regression control stayed ineligible. However, it only count-checked the raw rows; the four mutation checks merely confirmed that altered JSON has a different SHA-256. It did not validate the frozen generator/schema row-for-row or run the mutations against its audit validation path, as D required. Its nominal pass therefore does not establish the preregistered method gate. The first outcome is preserved without rerunning the candidate or formal auditor.

A separately versioned post-run verifier regenerated all 4,160 records from the frozen seed, independently recomputed both estimates, preserved `UNKNOWN` under low support, and rejected all four effective corrupted-record controls. This strengthens the internal consistency evidence but was not preregistered, so it does not replace the formal HOLD. Its exact command and stdout are retained in `posthoc_audit.stdout.txt`.

Raw ledger SHA-256: `b6245ff2f2afee4b97ad4f63ff69fa7af26aa8011ebc4256753775593741ea04`. Full machine output and stdout are retained in `formal_01/`; [RESULT.json](RESULT.json) records the post-run disposition. The candidate outcome is preserved with no retry.

## Execution and limits

Both frozen commands ran once, with no retries. Execution used host CPython 3.14.5 and the standard library. OrbStack reported Engine 29.4.0 linux/aarch64, but read-only inspection of the cached `python:3.12-slim` image failed on a missing containerd blob (`operation not supported`). No pull, build, or container was attempted. This result is host-only and says nothing about container isolation or resource enforcement.

All respondents, thresholds, ties, missing answers, lapses, and choices were generated synthetically from the preregistered fixture. The test does not measure actual preference or response behavior. It does not test a GUI, application, model, task, route, or user. No T0 pass is established, and this output cannot justify a user-value threshold, production policy, promotion claim, or adoption decision.

## Reproduction

Source and protocol hashes are in [FREEZE.json](FREEZE.json). The post-run revalidation can be inspected by running from the repository root; this is a separate post-run check and does not promote the formal result:

```sh
python3 -B research/analysis/user_worthwhile_benefit_7411_t0_a01_20261004/posthoc_audit.py
```
