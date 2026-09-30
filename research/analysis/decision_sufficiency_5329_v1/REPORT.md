# Issue #5329 — decision-sufficient evidence compression

## Disposition

`PASS_FINITE_CONTRACT_ONLY` after a post-hoc raw-only audit correction. The initial independent auditor's no-op mutation test failure is retained unchanged in `audit.json`; the corrected audit is `audit_v2.json`. This establishes exact behavior of the declared finite contracts only, not real evidence sufficiency or system security.

## H/T/D/C/U

- **H:** A consumer-specific summary can preserve every declared decision with fewer bytes than raw evidence. Label-only compression can yield unsafe PASS when a downstream consumer treats the label as sufficient; fail-closed profiles should turn missing required evidence into UNKNOWN.
- **T:** Exact enumeration of 12 hand-authored traces × 6 consumers × 5 policies (360 rows): LABEL_ONLY, RAW_TRACE, FIXED_SUMMARY, DECISION_SUFFICIENT, ADVERSARIAL_COMPRESSION. The raw decision oracle and profile requirements are frozen in `FREEZE.json` and the code. Metrics: decision disagreement, unsafe release PASS, UNKNOWN, and compact-JSON UTF-8 bytes.
- **D:** Frozen input/source/gates; raw output; independent exact audit; corrected mutation-control audit; report and byte hashes. `DECISION_SUFFICIENT` must have zero mismatches and lower bytes than RAW_TRACE; label-only must expose a dangerous counterexample; adversarial omission must not preserve false certainty; all four mutation controls must be effective.
- **C:** Finite records and predicate meanings are stipulated. There is no learned or probabilistic compressor, no actual multimodal evidence, no runtime/token latency, and no independently sampled population.
- **U:** Real consumers may depend on fields not in a declared profile; field semantics can be wrong; adaptive consumers and distribution shift are outside this proof; audit cost and raw-digest storage overhead are not included in byte totals.

## Exact result

The host enumerator emitted 360 rows. `DECISION_SUFFICIENT` matched the raw oracle on 72/72 consumer-trace pairs, with 4 UNKNOWNs also present in the raw reference. Its summaries used 4,971 compact-JSON bytes versus 11,808 for raw evidence (57.9% fewer bytes for these records; raw digest/transport overhead common to all rows is not modeled).

| Policy | Decision mismatches / 72 | Unsafe release PASS | UNKNOWN rows | Encoded bytes |
|---|---:|---:|---:|---:|
| LABEL_ONLY | 51 | 5 | 48 | 2,766 |
| RAW_TRACE | 0 | 0 | 4 | 11,808 |
| FIXED_SUMMARY | 44 | 0 | 48 | 5,094 |
| DECISION_SUFFICIENT | 0 | 0 | 4 | 4,971 |
| ADVERSARIAL_COMPRESSION | 68 | 0 | 72 | 3,951 |

The adversarial profile drops a required field and returns UNKNOWN for all 72 rows, not a false PASS. This is fail-closed but unhelpful, not an efficacy win. The label-only baseline exposes five unsafe PASS cases when a release consumer blindly trusts the status label. The fixed summary saves bytes but loses 44 declared consumer decisions.

## Audit failure and correction

The first auditor's four-control suite included `force_release_pass`, but its selected row already had decision PASS; the mutation was a no-op. `audit.json` is preserved as emitted and reports `all_controls_rejected=false`, so the original gate failed despite zero row-level disagreement. The simulation was not rerun. `audit_v2.py` applies the same raw-only oracle/accounting check to the identical raw SHA-256 `ABBFD07E541DAE643EAC7FE42DD630B1A55CCDA75A52C66444A35CC1CC4AD705`, choosing a non-PASS release row for that mutation. V2 reports zero disagreements and rejects all 4/4 effective controls. This is a disclosed audit correction, not a changed data/gate or new empirical allocation.

## Scope

Python 3.12.10, Windows x64 host; no model, GUI, network, Docker, or external effect. Docker was not used because this exact finite relation is analytically enumerable and has no environment-dependent behavior; per repository method, container experiments are reserved for the unresolved OS/timing/population residual, not used to add ceremony to the same finite proof. No broad safety, causal validity, product, or runtime claim follows. A practical next rung must freeze real consumer contracts and test whether their declared required fields are complete on a genuinely independent evidence corpus.
