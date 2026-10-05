# Additive wire-type correction over retained data

The original 24-trial/56-waiter candidate, raw, frozen v1 auditor, five source
pins, first outcome, all 42 original delivery files and their 41-entry manifest
remain unchanged. This directory adds a separately versioned posthoc auditor;
it does not consume another socket allocation or relabel the original PASS.

## Known original blind spot

The v1 wire-decoding check uses Python dictionary equality. A wire JSON answer
of 1 or 1.0 compares equal to the recorded True, even though the recorded answer
is subsequently checked with `is True`. Changing only a response wire frame
and its matching hash therefore escapes the frame-to-record binding. A copy of
the first trial/rpc-0 establishes this for server_sent, client_received and both,
with each numeric scalar: six distinct endpoint/type controls. Original saved
wire answers are all true; no disagreement in the original scope/count result
is found. This does not establish that v1 rejects every other forgery.

The original `PASS_SOCKET_SCOPE_TRANSFER_SCOPED` remains the first recorded
result of its predeclared eight controls. Its broader type-integrity reading is
qualified by this known false acceptance. Read the original README as that
historical result together with this qualification. Pending content proposals
were placed on author HOLD before the correction. Their votes are not copied.

## H/T/D/C/U fixed before the supplemental CLI

- **H:** type-sensitive recursive JSON comparison closes these wire numeric
  aliases while preserving the original authored cohort/count interpretation.
- **T:** read the unchanged 126 saved transport events; call the frozen v1
  structural/scope oracle, then compare each decoded wire value with its stored
  JSON value using canonical JSON. Run eight original and six added copied-data
  controls. No producer, socket, toolkit or model is imported or invoked.
- **D:** prospective source/input/interpreter/JSON-module hashes must match;
  unchanged retained raw must pass; all 14 corruptions must reject for their
  stated reason; all six original v1 false acceptances must remain reproduced.
  A new exclusive output path and 30 s / 1 MiB bounds apply to one supplemental
  ordinary CLI invocation, zero retries. Any first failure is retained.
- **C:** corruption controls are authored and known during development. This
  is retrospective adjudication of saved data, not a new observation or a
  prospectively stronger version of the original experimental gate.
- **U:** only the specified finite corruptions are exercised. No arbitrary
  forgery resistance, strict duplicate-key JSON policy, independent external
  wire capture, current source identity, natural demand, latency, GUI, effect,
  authority, runtime adoption or general safety is established.

The explicit added gate serializes parsed JSON with sorted keys, compact
separators and nonfinite-number rejection before comparison. It distinguishes
true, 1 and 1.0 recursively. It does not require lexical byte equality of
equivalent JSON whitespace/key order. The stored JSON is still bound by all
the unchanged v1 schema, scope, transcript and caller gates.

| Name | 日本語の意味・定義 | SI単位 | 範囲・前提 | 型 |
|---|---|---|---|---|
| decoded | 保存wire bytesをJSONとして復号した値 | 非物理データ | 元の復号・hash検査後 | JSON複合値 |
| recorded | 同じevent内のrequestまたはresponseの記録値 | 非物理データ | 元のschema・scope検査後 | JSON複合値 |
| wire_events | 保持された通信eventの個数 | 1（無次元の個数） | 固定rawの126件 | 整数スカラー |
| controls | 有効な改変コピーの個数 | 1（無次元の個数） | 元8件＋追加6件 | 整数スカラー |
| timeout_seconds | 補正CLIの停止上限 | s | 30、性能測定ではない | 整数スカラー |
| raw_sha256 | 変更していない原rawの識別子 | 非物理識別子 | 実bytesから計算 | 文字列 |

## Construction and retained review

The initial supplemental scaffold delegated to v1. One captured RED invocation
ran four test methods and failed all six added subcases. Its source snapshots,
hashes, actual exit 1, UTC and logs are retained. The single correction then
passed all four methods normally and under -O, including original controls,
six reproduced v1 acceptances and unchanged counts. These construction checks
use only saved-data copies. They are separate from the supplemental CLI, whose
outcome will be retained in RUN_REPORT.md and run-01/ after the prospective
freeze. Original absolute private paths in construction logs are replaced
only as explicitly bound by RETENTION.json; originals remain private.

For subsequent retained-only review from this directory:

```sh
python3 -B -m unittest test_audit_v2 -v
python3 -B -O -m unittest test_audit_v2 -v
```

These four methods never call the socket candidate. The one supplemental CLI
allocation is recorded by run_once.py, FREEZE.json and its exclusive output
receipt; do not repeat its run-01 allocation. Raw-only adjudication with a
separate new output is ordinary review, not permission to rerun the primary.

For current scientific delivery, read RUN_REPORT.md alongside the unchanged
original README. Main integration still needs a new fixed content proposal,
eligible nonauthor approvals, a fresh exact current-base/tree check, actual
GitHub conditions and conditional application. Common deadline is unconfirmed
and is not set/reset by this correction.
