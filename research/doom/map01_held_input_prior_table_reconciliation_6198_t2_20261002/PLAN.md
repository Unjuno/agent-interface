# #6198 T2 — audit-only prior interval-table reconciliation

## Lineage

The first #6175 posthoc table is retained at #6178. Successor #6198 replayed its pinned analyzer and logs, retaining candidate JSON and a raw-only audit; #6203 currently remains `HOLD_FROZEN_D_PRIOR_TABLE_RECONCILIATION_NOT_RETAINED` because the #6175 table was not an input to that retained audit. This is an audit-only successor to reconcile those already-retained artifacts. It must not rerun the historical analyzer, #6198 candidates, or #6203 auditor, and it does not alter any predecessor outcome.

## H / T / D / C / U

**H.** An independent audit over the retained #6198 candidate JSON and the frozen #6175 table will either match every completed interval row at the table's stated 0.001 ms display precision, match the exact aggregate summaries at 1e-9 tolerance, and match the one verified interruption exactly, or expose a discrepancy.

**T.** Freeze the source commits and Git blob identities of the two candidate JSON files from `research/6175-held-input-raw-receipt-t1-20261002` (commit `0032dfd4ab08343b81816a4e21192de345cca226`) and the prior `AUDITED_INTERVALS.json` from `research/6175-held-input-fulltrace-20261002` (commit `22610459ba04db1ac9064a962b78da0d8a528497`). Retain the GitHub MCP UTF-8 file responses as local JSON inputs and record local SHA-256 independently; upstream Git blob IDs are provenance identifiers, not recomputed from the text transport. Predeclare an independent standard-library auditor that checks local input hashes, row cardinality and identity, each displayed rounded bound, candidate-derived sums/medians/fractions, prior exact aggregate summaries, and the interrupted v39 row. Run construction mutation tests before freezing; then invoke only this audit once. Candidate invocations: 0. Historical analyzer invocations: 0. Retries: 0.

**D.** `PASS_PRIOR_TABLE_RECONCILIATION_SCOPED` only if source Git blobs match; exactly 11 v38 and 27 v39 completed rows map one-to-one by (decision id, step); keys/requested duration agree; each lower/upper/width display agrees within 0.000500001 ms; candidate aggregate fields equal independent recomputation and prior exact summaries within 1e-9; the one v39 interrupted row exactly matches identity, keyset, timestamps, classification and duration and is excluded from completed totals. Otherwise retain `FAIL` with differences; no retries.

**C.** A pass supplies retained independent evidence that #6198's candidate replay matches #6175's published per-decision table and exact aggregates. It may address the specific missing reconciliation gate noted in #6203, subject to review of scope and provenance.

**U.** This is an audit over two prior derived artifacts, not raw event logs and not new observations. It cannot reconstruct physical key occupancy, useful-feedback onset, causal v38/v39 differences, safety, live control, gameplay, or human tempo. A pass does not close #59 or replace #5156 instrumentation.

## Environment and integrity

- Allocation: `MAP01-HELD-INPUT-PRIOR-TABLE-6198-T2-20261002-01`.
- Current main at freeze: `4cf0a3dfde1219671b671bf0a9079a11dcb2e159`.
- Host CPU / Python standard library only. No Docker, model, network in the auditor, GUI, game, input, or task effect.
- Docker Desktop service is Stopped/Manual and Engine inventory requests are unresponsive. No service/process/container is changed. This data-only reconciliation has no container-dependent semantics.
- Candidate reruns: 0; T1 auditor reruns: 0; this new audit invocation: 1; retries: 0.
