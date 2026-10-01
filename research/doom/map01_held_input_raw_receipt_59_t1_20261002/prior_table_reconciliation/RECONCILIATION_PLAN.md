# #6198 prior-table reconciliation supplement

Allocation: `MAP01-HELD-INPUT-PRIOR-TABLE-RECONCILIATION-59-T1-20261002-01`
Parent: Issue [#6198](https://github.com/Unjuno/agent-interface/issues/6198), PR [#6203](https://github.com/Unjuno/agent-interface/pull/6203)
Parent PR head at freeze: `0032dfd4ab08343b81816a4e21192de345cca226`

## H / T / D / C / U

**H — hypothesis.** The exact retained #6198 candidate JSON outputs reconcile to every row at the displayed 0.001 ms precision, all nine reported exact aggregate fields per trace within 1e-9 ms, and the exact v39 interrupted receipt in #6175's published transcription. This can close the review's retained-evidence gap without rerunning candidates or the original auditor.

**T — test.** Run the isolated, newly authored read-only comparator `reconcile.py` exactly once against candidate files whose SHA256 identities are frozen below and the exact prior table with both SHA256 and Git blob identity frozen below. The comparator checks 11 v38 + 27 v39 completed rows; row identity/requested duration; rounded lower/upper/width; nine exact aggregates per trace; derived fractions; and v39 interruption identity, keys, timestamps, duration, and exclusion from completed totals. Seven construction/mutation unit tests must pass before the formal run. Candidate invocations: 0. Original auditor invocations: 0. Supplemental comparator invocations: 1. Retries/substitutions: 0. No model, network, GUI, game input, or task effect. Host CPU only.

**D — decision.** `PASS_PRIOR_TABLE_RECONCILED` only if the frozen input identities match, the comparator exits 0, all 38 row identities reconcile, 18 aggregate fields pass the 1e-9 ms tolerance, the interruption receipt matches, and the result/hash manifest is retained. Any mismatch or execution error is recorded as FAIL/STOP; do not retry or alter frozen inputs.

**C — counterfactual.** This is a document-to-document audit supplement, not a candidate replay, original auditor rerun, new observation, or independent validation of the source experiment. A pass means the retained #6198 outputs agree with the published #6175 transcription under its stated rounding and precision rules. The table explicitly identifies itself as a posthoc transcription, not the original candidate JSON.

**U — uncertainty and scope.** Agreement cannot repair missing original #6175 raw receipts or independently establish that the transcription faithfully represents those absent artifacts. It does not establish physical key occupancy, exact key-up, useful feedback, causality, live safety, game success, latency benefit, or product benefit. Docker Desktop is unavailable (service stopped; engine did not answer); no shared runtime is started or modified because the allocation belongs to another owner and this audit has no container-dependent semantics.

## Frozen identities

- Candidate v38 SHA256: `55771151887660b4a264d9e788410e12e2e6e45ca4f4c9d96db1a5f93e85e5f1`
- Candidate v39 SHA256: `49a47182f6d6f3fdb944224882be5716a0452b2cc88beee51b482ef915be5fc0`
- Prior table SHA256: `2aab450e687cce4b912a83d548b9ab76165ed1826110e7506468efe2891ef7df`
- Prior table Git blob SHA1: `b84cddc6d884e10e8a5e9baf202210923c558c57`
- Comparator SHA256: `f523d2f103e4f326919b6e6fbcf407f88b6771bfb624dbdde16cf51c361c8109`
- Tests SHA256: `c01d655b18daeccb0da7593481314b6fccb26f47312ebe3df1bb53eac6af8e91`
- Parent PR head: `0032dfd4ab08343b81816a4e21192de345cca226`

Formal command (one invocation only):

```powershell
python -B research/doom/map01_held_input_raw_receipt_59_t1_20261002/prior_table_reconciliation/reconcile.py --output research/doom/map01_held_input_raw_receipt_59_t1_20261002/prior_table_reconciliation/RECONCILIATION.json
```
