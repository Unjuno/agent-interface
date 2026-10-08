# T2-01 audit-only execution record

- Allocation: `MAP01-HELD-INPUT-PRIOR-TABLE-6198-T2-20261002-01`.
- Current main at freeze: `4cf0a3dfde1219671b671bf0a9079a11dcb2e159`.
- Retained candidate JSON source: #6203 head `0032dfd4ab08343b81816a4e21192de345cca226`; upstream Git blobs v38 `7115725d2aaa76b95221e0d0b6b407dd8704b6d9`, v39 `004891e1b58741ff39ef0776fee9717b3174f260`.
- Prior table source: #6178 head `22610459ba04db1ac9064a962b78da0d8a528497`; upstream Git blob `b84cddc6d884e10e8a5e9baf202210923c558c57`.
- Local UTF-8 input SHA-256 values: see `FREEZE.json` and `SHA256SUMS`.
- Pre-audit suite: `python -B -m unittest -v test_audit_reconcile.py` — 8/8 passed.
- Syntax: `python -B -m py_compile audit_reconcile.py test_audit_reconcile.py` — exit 0.
- Audit command, invoked once: `python -B audit_reconcile.py candidate_v38.json candidate_v39.json prior_audited_intervals.json results/t2-01/audit.json` — exit 1, `FAIL_PRIOR_TABLE_RECONCILIATION`.
- Audit findings: 11/11 v38 and 27/27 v39 row identity joins; all rounded numeric rows and exact aggregates matched; interrupted v39 matched; the frozen keyset comparator emitted 38 errors because the prior completed-row table has no keyset field.
- Historical candidates rerun: 0. Historical auditor reruns: 0. New auditor invocations: 1. Retries: 0.
- Scope: offline reconciliation of retained derived artifacts only; no raw log replay, model, GUI, game, user input or external effect.
