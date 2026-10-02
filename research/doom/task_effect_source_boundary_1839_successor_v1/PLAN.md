# Issue #1839 successor A01 — source-bound missing-effect boundary

## Lineage and non-duplication

Issue #1839's original 13-row synthetic contract, the #1859/#1865 cross-record task-effect ledger, #2100 physical-occupancy evidence, and the read-only #4193 v3 HOLD remain unchanged. This A01 asks a narrower new question: when a retained producer log has valid physical DOWN/UP receipts but no positive scorer transition, can a source-only independent checker preserve `UNRESOLVED_NO_TASK_EFFECT` and reject attempts to synthesize a task effect from weak or absent evidence? It does not rerun the earlier ledger or claim a new endpoint.

## H / T / D / C / U

**H.** On the exact retained #4193 source, an independently implemented source-only audit will reconstruct six session schemas and three attack physical joins while leaving all six sessions without a positive endpoint unresolved; six frozen malformed/misattribution probes will be rejected, with zero authority fields.

**T.** Freeze current main, this package, and `research/doom/map01_v12_attack_task_effect_live_v1/RAW_USED.json.xz` by SHA-256 before execution. Run the one-shot candidate in a fresh, network-disabled OrbStack container; save stdout, stderr, exit code, and result bytes. Then run a separately invoked audit container which reads only the frozen raw and candidate bytes and independently parses producer events/samples; it must not import candidate code. Do not edit or overwrite either frozen output after the first candidate invocation. No live runtime, GUI, model, game, OS input, GPU, or shared CI container.

**D.** `PASS_SOURCE_BOUND_NO_EFFECT_SCOPED` iff source hash and exact session set match; all 3/3 attack DOWN/UP joins independently reconstruct; all 194 samples have exact schema/types and strictly increasing same-session timestamps; attack and no-input positive endpoints are 0/3 and 0/3; disposition stays `UNRESOLVED_NO_TASK_EFFECT`; authority-grant count is zero; and the audit independently rejects all six frozen probes (ghost actuation, state-only promotion, program-terminal promotion, duplicate effect ID, effect before DOWN upper bound, unmeasured cross-clock event). Any candidate/auditor disagreement is `FAIL_AUDIT_MISMATCH`; evidence promotion is `FAIL_EFFECT_LAUNDERING`; execution/integrity failure is retained as STOP/HOLD without rerun.

**C.** The retained corpus has no positive scorer endpoint and therefore tests refusal/absence boundaries, not sensitivity to a true effect. The fixed schedule contains one actuation per attack session. Its existing v3 machine result is malformed and remains untouched; A01 reads the original source directly. This is an offline deterministic source-compatibility study.

**U / stop.** No new live endpoint, causal link, scorer truth, recovery efficacy, MAP01 completion, safety, latency, human-tempo, or product claim. Stop after this one candidate/auditor pair; no retry, tuning, live follow-up, or old-result rewrite.

## Frozen inputs

- Intake main: `6fdfa6b2e2bbb13a58a235dae5499676d7dd417f`.
- Original compressed source SHA-256: `0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740` (7,392 bytes).
- Runtime: OrbStack Docker Engine 29.4.0, `linux/arm64`; cached `python:3.12-alpine`, immutable image ID/digest recorded in `FREEZE.json` before execution.
- Candidate/auditor each have a separate output path; no network and read-only root/source mounts.
