# Cancellation at a shared completion timestamp — Issue #6501

New boundary characterization `6501-CANCEL-ORDER-HOST-20261003-01a0ff2d`.
Policy FINAL-v5; worker thread 01a0ff2d-eb8e-70e0-82bb-ba3bf0c79b5c.
Base/source commit: 11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d.
This does not rerun retained T0/T0b, execute their scheduler, or change historical results.
It calls only the retained `_classify` helper against new inputs.

## H / T / D / C / U

- H: a timestamp-only cancellation check cannot distinguish cancellation before
  versus after delivery when both map to the same timestamp. Strict `<` admits
  a cancelled waiter; conservative `<=` rejects a waiter whose delivery preceded
  cancellation. An explicit local total event order decides this finite contract.
- T: exhaustively enumerate truth TRUE/FALSE, each of two callers' cancellation
  time absent/4/5/6 ms, and all six order labels for cancellation-a,
  cancellation-b and shared return at 5 ms. 192 assignments, 384 waiter decisions.
  Different labels can induce the same actual order when timestamps differ:
  these are exhaustive finite assignments, not independent statistical trials.
  Compare pinned timestamp `<`, conservative `<=`, and event-ordered delivery.
  All other target/deadline/freshness fields are fixed eligible controls.
  Independent raw-only auditor uses the event prefix before return as oracle.
- D: PASS_BOUNDARY_CHARACTERIZATION_SCOPED requires exact source identity,
  all 192 assignments and 384 decisions, strict comparator 48 wrong admits and
  zero wrong rejects, conservative comparator zero wrong admits and 48 wrong
  rejects, ordered comparator zero mismatches, and 8 effective corruption
  controls rejected. Any mismatch or source/output/exit gap is FAIL/HOLD;
  never tune or retry this one-shot retained invocation.
- C: the old model may intentionally serialize equal timestamps as return-first.
  That is consistent with its ten historical fixtures; the new contract adds
  both intra-bucket event orders. This is model-boundary evidence, not proof of
  a production singleflight vulnerability or an invalidation of T0b.
- U: synthetic time is not wall-clock performance. A real backend may lack a
  trustworthy sequence receipt; inventing one is not allowed. No GUI/effect,
  runtime authority, distributed ordering, physical release or efficiency claim.

## Contract and dimensions

| Symbol/field | 日本語の意味・定義 | SI単位 | 範囲・前提 | 型 |
|---|---|---|---|---|
| timestamp_ms | 合成イベントの時刻値 | s (格納は ms、1 ms = 0.001 s) | 4, 5, 6; 実時間測定ではない | 整数 |
| sequence | 同一時刻内の宣言済み順序 | 1 (無次元) | 0, 1, 2; 本有限モデルのみ | 整数 |
| caller | 独立した要求の識別子 | 非物理識別子 | a または b; 取消は要求ごと | 文字列 |
| truth | 共有する記述的検証結果 | 非物理値 | TRUE/FALSE; 行ごとに固定 | 列挙文字列 |
| decision | 返却時点の要求判定 | 非物理値 | CANCELLED_WAITER/ADMISSIBLE_TRUE/ADMISSIBLE_FALSE | 列挙文字列 |

Sort events lexicographically by (timestamp_ms, sequence). At the shared return,
only earlier cancellation of the same caller forbids delivery. A later cancel
does not retroactively change the observed delivery. Nothing grants input authority.
Deadline is 10 ms; validity interval [0,20] ms and generation 1 are fixed.

## Execution boundaries

Host Windows 11, CPython 3.12.10, stdlib only; one child at a time, timeout 20 s
per child, output <=1 MiB. No WSLc/container/GPU/model/GUI/network call by the assay.
Exclusive-create run01 directory and files. Candidate once; raw-only auditor once
conditional on candidate exit 0. Runner records real UTC start/end, argv, exit,
stdout/stderr, source/raw hashes. Construction checks are separate and repeatable.
Construction exposed list/tuple serialization in an in-memory auditor check;
the fixture representation was corrected before this freeze. No formal run was
consumed by construction. The initial stub had two expected failing unit tests;
the completed comparator and audit controls passed six tests.

## Source identity

retained_candidate.py is the exact 4,338-byte Git blob
473529819d9fe6dec29cf113bd49a2c7de872236 from
research/analysis/scope_typed_singleflight_6501_t0b_20261002/candidate.py.
It is copied unchanged for byte identity and imported only by the new assay.
The original run()/main() are never called. All sources are frozen by FREEZE.json.

## Navigation and publication

The additive package is evidence/construction only. No runtime import, workflow,
root acceptance gate or legacy fixture is changed. Reviewer approvals are
required by FINAL-v5 before main reflection. Common fleet deadline is unconfirmed;
this is a bounded local work segment, not an extension or new fleet deadline.
