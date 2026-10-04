# Teardown receipt/witness consistency review — #5156

## Result

**FAIL_TEARDOWN_WITNESS_COVERAGE_SCOPED** at PR #6865 head
`a424f2c32c5550989cfdbc9a4a4f89e69454fb20`: both its preserved legacy auditor
and new supplement accept all fifteen authored contradictory teardown records.
The unchanged positive passes all three independent consistency predicates.
The separately implemented raw-only checker reconciles all sixteen rows, their
single-leaf changes and hashes. All five directed checker-integrity corruptions
are rejected; the unchanged control passes.

| Copied-raw change | Cases | Supplement false accepts |
|---|---:|---:|
| Appended owner witness differs from receipt: owner, intent, or verified time | 6 | 6 |
| Receipt verification one ns outside caller interval | 6 | 6 |
| Receipt verification one ns different from owner snapshot, within interval | 3 | 3 |

The original PR manifest matches 45/45 files and its existing pure regression
accepts the unchanged control and rejects its ten declared negatives. This new
assay does not falsify those outcomes or assert that the original live A18 raw is
incorrect. It establishes an additional exact consistency boundary. Adopt the
three added consistency checks before relying on teardown chronology/witnesses
in a future live bridge; the author is preparing a separate repair revision.

## Source basis

`source_derivation/input_transition_owner_v3.py::call` brackets the synchronous
inner `release` call and decorates a copy of its returned owner-release record.
The generated owner appends that same record to `records` before returning it;
its verification timestamp is sampled inside the synchronous call.
`source_derivation/candidate.py` snapshots the owner records before/after the
single and two-key teardown, retaining the appended rows, and retains the final
snapshot after owner close. Thus three local consistency predicates are justified:

1. The teardown verification timestamp lies between caller start and return.
2. The receipt projection, excluding the two caller-only timestamps, occurs in
   the final owner snapshot.
3. For the single/two-key cases, the appended witness equals that projection.

The cancellation teardown has no appended-row field and legitimately has null
intent after autonomous cleanup; no new appended-row or non-null-intent rule is
invented. Future lease deadlines are excluded. These predicates concern recorded
consistency only and do not authenticate the actual backend.

Four source-derivation files match their A18 frozen SHA-256 identities exactly.
They are retained for reading only and are never imported/executed in this review.
`input_owner_v11.py` generated inside A18 is distinct from the similarly named
root telemetry wrapper; the build source specifies the generated-owner record.

| Field | 日本語の意味・定義 | SI unit | Range/assumptions | Type |
|---|---|---|---|---|
| release_call_started_ns | 同期release呼出し直前の単調時計値 | s, stored as ns | One clock; arbitrary origin | Exact integer |
| release_call_returned_ns | 同期release呼出し直後の単調時計値 | s, stored as ns | Same clock; at/after start | Exact integer |
| verified_ns | ownerが中立入力状態を確認した記録時計値 | s, stored as ns | Recorded witness; not physical/application time | Exact integer |
| owner_id | 解放記録を作成したowner識別子 | Nonphysical identifier | Fixed retained owner | String |
| intent_token | 記録された入力意図識別子 | Nonphysical identifier | Null legitimate after cleanup | String or null |
| verified | owner記録の確認結果 | Dimensionless truth | JSON true differs from integer 1 | Exact Boolean |

## Execution and preservation

Worker/session `01a0ff58-2d0b-7eb1-8b33-c8b69e63563a`, FINAL-v5; dedicated
Windows host CPython 3.11.9 process and private source/output copy. The exact
platform, Python version, process identity and UTC start/end are in
`review-01/probe.json`; this report makes no timing/performance claim.

The prospective reviewer freeze SHA-256 is
`0840d7939f994f790240b757c31d0ad66fb372ec95b99f6d52fbcae6768b213f`.
The original probe and raw-only reconstruction each executed once, with shell
exit 0. `review-01/` preserves every first result, including accepted negatives.
`controls.json` records five separate private-copy integrity controls. No
backend/input/model/GUI/container/GPU or formal A18/C01 invocation occurred.

The source copy of the original raw SHA-256 is
`0db56f8f3560b2a76aec0aeffe728586533b5b95a82a19cee3c425ff99eddf2e`.
Original A18/C01 programs, raw, allocations and scientific dispositions are
unchanged. This package owns only its additive evidence path; no runtime source,
shared index or author branch was edited. No main application or vote is claimed.

## Limits and disposition

These fifteen authored finite counterexamples are not independent statistical
samples. A one-ns mutation checks an exact equality/ordering contract; it does
not measure timer resolution, accuracy, latency, physical key-up, application
consumption, continuous input neutrality, MAP01 efficacy or human tempo.

The independent checker implements the stated predicates directly and does not
import either tested validator or the mutation generator. It is a separate
implementation by this reviewer, not another person's content approval or
authenticated backend evidence. Common fleet deadline and N were unavailable;
neither was reset or expanded. No shared lease/input was acquired or emitted.

The bounded author correction is tracked on
[PR #6865](https://github.com/Unjuno/agent-interface/pull/6865#issuecomment-5964139503).
Its changed head requires fresh review; the old proposal's votes cannot approve
the new content. Research goal and parent #5156 remain unresolved.

## Separately frozen revision-2 follow-up

At head `f0ca86d295265f7ee55da2d4805b5ab471944d3a`, the author added the three
teardown predicates in a separate revision without changing C01. The independent
follow-up reads the original sixteen reviewer rows rather than regenerating them:
original accepted, all fifteen negatives rejected, all sixteen match the unchanged
raw-only oracle. This resolves the original targeted counterexamples in v2.

Two separately prospectively identified Boolean-to-integer controls still pass
v2: `single.owner_rows_appended[0].verified=true` changed to `1`, and the matching
cancel final owner snapshot's `verified=true` changed to `1`. Receipts keep true.
The unchanged type-sensitive raw-only projection checker rejects both, while
v2's Python dictionary equality accepts both. This qualifies exact JSON witness
identity, not the unchanged physical data. Type-sensitive comparison is the
small sufficient repair; no new schema framework or allocation is needed.

`FOLLOWUP_PLAN.md` and `FOLLOWUP_FREEZE.json` preserve the separate identity and
prospective source boundary (freeze SHA-256
`ed96519c8346c77e7b628328f608f77d89f381eed7779d1147f81e3a9a51461a`).
`followup-v2-01/result.json` retains all decisions and both copied raw controls.
This does not expand or relabel the original fifteen-row matrix. The technical
follow-up is recorded on
[PR #6865](https://github.com/Unjuno/agent-interface/pull/6865#issuecomment-5964217806).
