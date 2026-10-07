# Issue #7059 T0 A02 — verdict-free redundancy ledger

## Purpose and relationship to A01

This is a new, one-shot allocation under the still-open Issue #7059. It preserves A01's `STOP_EXECUTION_COUNT_MISMATCH` unchanged. A01's content-level audit over its retained output is not promoted into an allocation-level result. A02 changes no scientific factor: it repeats only the authored measurement-ledger method rung with new output paths and an exclusive-create candidate writer, because A01's first candidate output was overwritten after an accidental second launch. This is not the T1 behavioral/model study.

## H / T / D / C / U

**H.** The measurement ledger can distinguish a harmless null contrast, a harmful missed check, fewer checks with unchanged correctness, a legitimate UNKNOWN, and an incomplete tool log while preserving fixed reviewer topology, evidence pool, caps, reducer, context identity, and peer-content-after-commit ordering.

**T.** Allocation `UNJUNO-7059-VERDICT-FREE-T0-A02-20261007-01`; main base `8c8b37424fdb43482412240868574813fae46c2e`; one pinned `node:26-alpine` linux/arm64 image, network disabled, configured 1 CPU / 128 MiB / 32 PIDs, source bind read-only, distinct output bind writable. One candidate process writes once to a new path using exclusive-create mode. After a successful candidate exit and hash capture, one separate auditor process reads that immutable output and writes to a distinct new path. No candidate/auditor CLI is launched by construction tests. No model, human, GUI, user data, GPU, native effect, or action authority is used.

**D.** `PASS_METHOD_SCOPED` only if the independent audit reconstructs all 10 case×arm rows, preserves two reviewers and identical evidence/tool budgets, classifies all five patterns as frozen, keeps peer content after both commits, and rejects all six integrity mutations. Any execution-count mismatch, missing raw digest, candidate/auditor error, mutation acceptance, or case mismatch is `STOP`/`FAIL_AUDIT`; no retry or overwrite.

**C.** A fixed synthetic ledger cannot establish model or human behavior; a roster phrase may change only prompt salience, and fewer reads may be efficient rather than harmful. A stronger raw schema may still share the same semantic assumptions as its fixture.

**U.** Method-only authored-record evidence. No social/cognitive mechanism, behavioral effect, model generalization, GUI task effect, latency, safety, or product claim. T1 requires a separately approved, blinded and adequately powered empirical allocation.

## Frozen record

`FREEZE.json` binds the exact fixture, candidate, auditor, construction test, Node image digest, exact role commands and one-candidate/one-auditor stopping rule. Formal outputs belong only under `results/candidate/` and `results/auditor/`. Existing files cause immediate stop; do not replace them.

## Formal result

`PASS_METHOD_SCOPED`: one candidate invocation exited 0 and produced a 57,758-byte raw ledger; one separate auditor invocation exited 0, reconstructed 10/10 rows across five cases and two roster-text arms, and rejected all six integrity mutations. Candidate SHA-256: `e6f40d961b88b1b328f6154a1a19af3a214552c6bde2689476135de0e37e7f01`; auditor SHA-256: `a5e1999ac1861717329f894707437a68fd5dc8abb4288165c0f165f7f90062c1`. See `REPORT.md`, `RUN_RECORD.json`, and `SHA256SUMS.txt`.

The synthetic truth table contains a harmful missed check that remains incorrect in both arms, a fewer-checks/same-correctness case, a valid UNKNOWN case, and a missing-tool-log case held in both arms. Therefore this run validates ledger observability and classifications only; it does not show that roster disclosure changes reviewer behavior or outcomes.

## Reproduction and custody

Run construction-only checks with `node --test test_construction.mjs`. The formal candidate and auditor commands and expected output locations are recorded in `FREEZE.json`; the read-only source mount is `/study`, candidate output mount `/out`, and auditor output mount `/audit-out`. See `RUN_RECORD.json` and `SHA256SUMS.txt` for the actual first outcomes, raw hashes, tool version and resource profile. Original A01 remains separately preserved in PR #8010.
