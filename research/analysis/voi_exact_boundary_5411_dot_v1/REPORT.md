# #5411: no declared decision discrepancy on the retained finite grid

Disposition: **PASS_NO_DECLARED_DECISION_DISCREPANCY**.

One independent exact-rational check of the original retained #5306 output
found no evidence for the suspected float/Decimal threshold defect on its
405 tuples. The predecessor runner was not executed or modified. This is a
finite arithmetic validation, not a new VOI performance or deployment result.

## Result

- All 405 ordered, unique input tuples match the literal frozen grid
- All 2,025 typed decision fields match exact arithmetic at the declared
  1e-12 threshold; strict-zero decisions also match on this grid
- All 3,645 numeric comparisons remain within the predecessor's separate
  1e-10 numerical-value allowance; all five retained summary fields reconcile
- Exact outcomes retain 45 premium-induced decision changes: 27 strictly
  dominated waits and 18 changed decisions that are exact value ties
- There are 58 exact VOI ties overall. The 18 above are a subset, not the
  complete tie count. Immediate-action margins have 27 zero ties and premium
  margins have 55
- Minimum nonzero absolute decision margin: 1/200 = 0.005
- Every exact decision margin is on the 1/200 lattice
- Maximum absolute binary numeric error: 1/703687441776640, approximately
  1.42e-15. There are 2,316 nonzero signed binary rounding entries, all retained;
  rounding alone is not a decision defect
- One checker invocation, exit 0, empty stderr; predecessor invocations and
  retries both zero

The exact minimum nonzero margin is five billion times the declared decision
threshold. This and the zero-tie reconstruction explain why small binary
rounding does not change these decisions. This statement is scoped to the
retained grid; it is not a general tolerance recommendation.

An independently checked boundary witness makes the distinction concrete:
`voi-option-258` has p=0.8, loss=1, sensitivity=0.8, false-pass=0.3 and delay=0.
Its exact observation-branch values are 29/50 and 1/50; exact net VOI is zero.
The retained binary net VOI is positive 1/9007199254740992, approximately
1.11e-16. The original 1e-12 predicate still correctly returns STOP.
“Exact strict-zero agrees” does not mean that removing tolerance from the
binary-float implementation is justified; this witness distinguishes them.

## H / T / D / C / U

H: a suspected near-tie float/exact discrepancy might exist in the retained
grid. The executed check did not find one.

T: independently reconstruct joint safe/unsafe observation masses with
fractions.Fraction, optimize admit/yield within each observation branch, and
compare every retained row. Keep declared-threshold, strict-zero, recorded
decisions and retained float-expression consistency distinct. Decode only the
existing raw transport, after exact source/artifact verification.

D: all frozen coverage, type, arithmetic, predicate and aggregate gates pass.
No arithmetic correction is justified by this result. The original synthetic
one-step result remains intact; the wider #5306 hypothesis remains untested.

C: the existing Decimal auditor already reported no errors. The added value
is an independently reviewed rational reconstruction that resolves #5411's
specific suspicion and preserves all exact margins/ties. The source and raw
are stipulated finite synthetic data, not a sampled verifier/task population.

U: no arbitrary-input floating-point guarantee, multi-step continuation-value
result, empirical calibration, real-time scheduling result, GUI effect,
model/provider call or production recommendation.

## Provenance and execution

- Source commit: 473c82de2b332b3937927b1f9061eea329541ef0
- Retained artifact commit: 77bfcf73184c948716c7837fa49bb4d714421fe6
- Original evidence merge: 4ac82a8f6caaa469ee635428f9cea135c7cb7d0b (#5419)
- Decoded original raw: 198,339 bytes, SHA-256
  fa237492dd6657da2b98a3b48bc994851e057a70df1c252fbe974a2a5ea22f3a
- Checker SHA-256: 8f45c128cdeb46aa00a314f0fdca4c1077123e21201e9d39b13fd7eff15f3442
- Source/input freeze SHA-256:
  69f994dde82c002de21ab7e8cf5ae15adc7789166b5df08db7cd27b07755be22
- [Prospective public freeze](https://github.com/Unjuno/agent-interface/issues/5411#issuecomment-5909847929)

Independent static review preceded execution. Four hand-derived construction
tests pass; original import/setup failures and review corrections are retained
as construction records, not evidence invocations. The reviewer caught typed
Boolean checking, fifth-summary coverage and FAIL-versus-STOP labeling before
the immutable freeze.

Environment: existing authorized cloud workspace, Linux x86_64 6.18.44,
CPython 3.12.14 standard library. One compute process on CPU 0, 128 MiB
address-space ceiling, CPU 9/10-second soft/hard bounds, 10-second wall alarm.
Reported peak RSS was 14,208 KiB. The recorded comparison/output window was
67,733,611 ns; process CPU at the receipt was 0.102701229 seconds including
initialization. These are resource receipts, not latency benchmark evidence.
The checker created no subprocess and made no external call. No Docker/OrbStack,
paid service/job submission, GitHub-hosted experiment, GPU, model or user-machine execution
occurred.

`evidence-01/EXACT_ROWS.jsonl` preserves every exact value, margin, predicate
and signed numeric error. `RESULT.json` preserves complete discrepancy/tie
lists and aggregates. `INVOCATION.json`, outer stdout/stderr/exit and
`SHA256.json` bind the first outcome. Do not rerun the consumed allocation.
