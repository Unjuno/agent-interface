# Prospective ordinary source comparison C01

This is a new bounded construction check for the two-line effect-start repair,
not a replay of any historical formal allocation. The first TDD baseline has
the explicitly weaker post-run identity qualification in TDD_FREEZE.json and
SETUP_NOTES.md. C01 will instead have a successful byte freeze before execution.

H: In a typed, sequential, explicitly comparable nanosecond-clock fixture,
the unchanged source accepts a matching effect observation earlier than recorded
execution start. Adding the recorded-start floor refuses it before any mutation
and preserves complete execution/request/release custody and later observations.

T: Load exact four-file baseline/candidate source snapshots in separate private
namespaces. Enumerate 2 arms × 3 effect statuses × 10 times × 3 identities =180
rows. Each row retains full before/after state, attempted receipt, admission,
error and terminal outcome. Times are0,399,400,599,600,700,799,800,1000,2000;
identities are matching, wrong command and wrong manifest. Accepted begin400,
recorded start600/end800/release900 and lease expiry1000 stay literal constants.
The baseline is the strongest existing source, including adopted temporal and
release guards; candidate changes only the two-line recorded-start predicate.

D: The separate raw-only literal oracle requires the complete ordered census,
type-sensitive exact JSON fields, source identities and full state custody.
Baseline accepts30 matching rows including12 pre-start rows; candidate accepts18
matching rows and zero pre-start rows. Both refuse60 identity mismatches without
mutation. All8 effective deep-copy corruptions must refuse: boolean/float aliases,
changed admission, lost execution after refusal, changed effect truth, missing
row, changed source identity and extra state. A runtime/serialization/audit error
is preserved and does not become PASS. No row is dropped or threshold revised.

C: A truthful monotonic backend/caller may already guarantee this relation.
The guard cannot establish truthful clock provenance, observation after the
final action or correctness of the reported application effect. Equality and
observations during execution remain admitted; receipt arrival is not observation
time. An execution-end floor or lease-based observation ceiling is not tested as
an adopted repair. Nominal non-record inputs and cancellation occurrence semantics
belong to separate owners and are not changed here.

U: Synthetic ordinary typed API behavior only. No physical/backend/GUI/model/
public-path/task/performance measurement, no authenticated clock, no concurrency
or arbitrary-time guarantee. The public MCP path does not consume this kernel.

| 記号 | 日本語の意味・定義 | SI単位 | 範囲・前提 | 型 |
|---|---|---|---|---|
| A | 受理されたbegin時刻。400に固定 | ns | 比較可能な合成時計 | 非負整数スカラー |
| S | execution receiptに記録された開始時刻。600に固定 | ns | A以上 | 非負整数スカラー |
| F | effect receiptに記録された観測時刻 | ns | 上記10値、同一合成時計 | 非負整数スカラー |
| E | execution receiptに記録された終了時刻。800に固定 | ns | S以上 | 非負整数スカラー |
| L | lease失効時刻。1000に固定 | ns | begin時の権限検査に使用 | 非負整数スカラー |

Each source/audit invocation uses one native stdlib child,30s timeout and2MiB
per captured stream; expected total evidence is below8MiB. No shared input,
backend, GUI/GPU/container/WSLc/model/provider/resource/apply lock or new worker.
Common deadline remains unavailable and is not extended. Initial invocations
are retained once each; ordinary construction repairs may use explicit new
versions with their first failures preserved, never historical producer replay.
