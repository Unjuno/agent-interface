# MotorState decoded-JSON boundary repair — Issue #2530

At exact main base `cb13a10dce358649458f5aea00947b8aa43fc5b8`, the pure dispatch
bridge converted wrong JSON container shapes before validation. Empty dicts could
become accepted event/key arrays, an empty array could become a pointer dict,
and a pair-list acknowledgement could become an accepted acknowledgement dict.
Unhashable enum values raised `TypeError` in both validator and dispatch bridge.

The repair checks context list/Mapping kinds before conversion and enum strings
before set membership. Valid Mapping interfaces (including MappingProxyType),
list copies, defaults, release visibility and confirmation rules are preserved.
There is no new authority, native backend call or task-effect inference.

## Executed ordinary engineering checks

| Check | First result | Repaired result |
|---|---|---|
| Eight new regression methods | 18 failures, 41 exceptions; exit 1 | Included in complete suite |
| Complete MotorState package | Not rerun as a baseline-wide suite | 24 methods pass; exit 0 |
| Same frozen 2,619 JSON cases/source | 806 reference mismatches, 746 TypeErrors, zero mutations | Zero mismatches/exceptions/mutations |
| Raw-only audit | Structural completeness passes; baseline counterexamples retained | Pass; all eight corruption controls rejected |
| Public receipt seam (four existing methods plus one new nine-case method) | 9 TypeErrors; exit 1 | 5 methods pass; exit 0 |

The corpus contains 2,420 adapter/bridge enum-product cases, 180 bridge container
shape cases across four dispatch statuses, 11 dispatch status cases and eight
legacy controls. Inputs and candidate/oracle hashes were frozen before either
corpus execution. The producer only invokes the APIs and records their outputs;
the auditor imports no production code and classifies preserved raw separately.
It compares JSON types recursively so `false`/`0` and nested `true`/`1` cannot
substitute for each other. Source identities include every exact original package
blob; candidate summaries bind the two executed production source hashes.

All eight decisive subprocesses retain actual UTC start/end, command, exit code
and complete stdout/stderr. The original triage file has no separate UTC/exit
receipt and is only a motivating observation. All private original bytes remain
unchanged. Public derivatives redact the author's filesystem prefix; PROVENANCE
records original/public hashes separately, and SHA256SUMS identifies these public
bytes. The initial regression log is deliberately retained as a failed result.

## Scope and independent use

Host: Windows 11, CPython 3.12.10, stdlib only. This is a finite synthetic JSON
boundary and ordinary regression repair under the resource-contention override,
not a new/repeated formal allocation. No native input, backend, GUI, model, GPU,
WSLc/container enforcement, physical release, latency or live task result was
measured. The bridge currently has package/test callers in the inspected runtime
scope. Its validator also serves the existing public CLI receipt presentation;
the exact six-file import/receipt dependency closure is byte-identical on base
and checked main `4bd391e6aa96fa20ebf8547a350a122f55d2e1ad`. The receipt check
uses the normal package imports and read-only receipt_bytes/view functions. It
confirms malformed enums become validation evidence with authority=none and
unchanged retained report/raw view. No new dispatch bridge CLI integration is claimed.

Pointer contents/list elements, general user-defined Python objects, schema
extensions and the existing non-Mapping result-release fallback are outside this
repair. Retained raw covers JSON values; MappingProxyType compatibility is covered
by the explicit unit test, not represented in the JSON corpus. Earlier Issue
#2530 experiment/STOP results remain unchanged.

`baseline/*.py.txt` and `tools/*.py.txt` are inert evidence. The three executable
runtime changes are only adapter.py, dispatch_bridge.py and test_json_boundary.py.
To audit without running a candidate:

```text
python tools/audit.py.txt cases.jsonl observed/before.jsonl CORPUS_FREEZE.json before
python tools/audit.py.txt cases.jsonl observed/after.jsonl CORPUS_FREEZE.json after
```

The auditor creates new output files and refuses existing ones. Use fresh copies
of the raw files in a separate output directory for these commands; do not alter
retained originals. To reproduce an ordinary candidate check, use a separately
materialized source tree and `python tools/candidate.py.txt SOURCE cases.jsonl NEW_OUTPUT.jsonl`.
This does not authorize any consumed formal run or shared resource.

Content approval, actual current-main planned-tree verification, GitHub conditions
and expected-base application are separate gates. This packet does not authorize
main or claim an approval. The common fleet deadline remains unconfirmed.
