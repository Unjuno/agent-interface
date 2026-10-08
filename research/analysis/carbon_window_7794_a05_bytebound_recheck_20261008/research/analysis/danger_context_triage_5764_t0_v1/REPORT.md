# Issue #5764 T0 — danger-context optional-audit triage

## Disposition

`PASS_METHOD_SCOPED` for the authored finite selector mechanics after the separately frozen v2 read-only audit. The one candidate outcome is retained unchanged. Audit-v1 remains `STOP_AUDITOR_FREEZE_SCHEMA_ADAPTER`; audit-v2 is the successful raw audit. This is not an empirical H pass.

The fixed four-slot comparison found five optional labeled failures in the 11-row optional population. DUAL selected three; EFFECT_ONLY also selected three. The #5435 SAFE_IDENTITY_BATCH adapter selected two, NOVELTY_ONLY and #5435 SEVERITY_ONLY selected zero, and chronological selection found one. Therefore novelty added no discovery beyond the linked effect signal on this fixture; a possible difference in which non-failure occupied the fourth slot is not an incremental-yield result. `CORRECTION.md` clarifies that the #5435 source's 64-hex digest in the original freeze is SHA-256, not a Git blob object ID.

## H / T / D / C / U

**H (unverified beyond T0):** Adding novelty to source/action-linked pre-audit effect-discrepancy evidence may discover more independently adjudicated nonmandatory failures at a fixed budget than novelty-only and the strongest eligible simple #5435 actionability/severity policy. T0 cannot establish this empirical claim. On the authored fixture, DUAL equals EFFECT_ONLY at 3/5; the dual signal shows no incremental discovery over effect-only.

**T:** One frozen 12-event stream with four observed novelty×effect cells, one unknown and one delayed effect, a same-time event with mismatched action lineage, and one mandatory hard event kept outside the optional ranking. The optional budget is four. Six fixed policies are replayed: DUAL, NOVELTY_ONLY, EFFECT_ONLY, #5435 T4 SEVERITY_ONLY, #5435 T4 SAFE_IDENTITY_BATCH, and chronological. The candidate reads only `preaudit_stream.json`; labels are in `sealed_outcomes.json` and applied after selection by the auditor.

**D:** The candidate completed once, exit 0. The independent v2 audit agrees with all six selector outputs, reconciles all 12 records and the mandatory event, and rejects 6/6 frozen mutations. This supports method-scoped replay only. No comparative/human/runtime hypothesis is promoted. The first audit's adapter failure remains preserved and disclosed.

**C:** All values and outcomes are analyst-authored. Only one small fixed stream and one fixed budget are used. The #5435 policies are adapted as preselection filters under the shared audit budget, preserving input order; this is not a replay of the complete responder-capacity T4 simulator. EFFECT_ONLY may already carry all useful signal; severity or identity batching may be misaligned with post-event audit ranking.

**U:** No real pre-audit signal availability, calibrated distribution, independent empirical labels, audit yield, harm probability, human/model fatigue, runtime safety, causal benefit, or product effect is measured. Missing/delayed E remains unknown and cannot imply safety. Critical events remain mandatory and are excluded from optional-yield gains.

## Audited comparison

| Selector | Optional failures found / 5 | Selected optional IDs |
|---|---:|---|
| DUAL | 3/5 | novel-harm-01, familiar-harm-01, familiar-harm-02, high-severity-benign-01 |
| EFFECT_ONLY | 3/5 | familiar-harm-01, familiar-harm-02, novel-harm-01, familiar-benign-01 |
| #5435 SAFE_IDENTITY_BATCH adapter | 2/5 | novel-benign-01, familiar-harm-01, novel-harm-01, familiar-benign-01 |
| NOVELTY_ONLY | 0/5 | high-severity-benign-01, novel-benign-01, novel-benign-01-copy, novel-benign-02 |
| #5435 SEVERITY_ONLY adapter | 0/5 | high-severity-benign-01 |
| Chronological | 1/5 | novel-benign-01, novel-benign-01-copy, familiar-harm-01, temporal-neighbor-01 |

The separate mandatory lane contains `hard-01`, labeled mandatory failure; it is preserved under every selector and is not included in the optional 5-failure denominator. Full population denominator: 12.

## Reproduction

The exact original commands and exits are in `EXECUTION.md`. The allocation is consumed: do not rerun its candidate, audit-v1, or audit-v2. Any future study must be separately authorized and frozen against a new eligible cohort; this package is not evidence that the synthetic labels or rankings transfer.
