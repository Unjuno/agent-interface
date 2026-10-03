# Aggregate receipt cannot identify terminal release in the snapshot model

The first fixed 36-row execution contains six complete receipt-projection equivalence
classes with opposite final input states. This supplies a constructive impossibility
argument for any decision based only on that projection under the declared assumptions.
It does not establish that a real backend permits these histories or violates its
stronger release guarantee.

## Model and exact source

Primary source is main `332da58a9b6b825c384a142dfb59d7ed2b8b774e`, with exact four Git
blobs retained in [SOURCE.json](SOURCE.json) and `frozen_kernel/`. The constructor's
current lower bound requires the release observation not precede the recorded start.
`RequestLifecycle.record_execution` checks identities, action count and a verified
empty release; `outcome().release_verified` is derived from that supplied release.
The receipt contains neither the last press time nor an event sequence. This assay
constructs valid typed inputs and reads those actual source outcomes. It invokes no
backend implementation.

One key A starts up. A press holds A; release-all makes A up, and its snapshot is
truthfully empty at that event. No unlogged/external input exists. All four modeled
events share an integer clock. Explicit order distinguishes equal timestamps. The
recorded start is 100 ns, end is 700 or 900 ns, press is 200/400/600 ns, and release is
200/400/600/end/end+100 ns. Receipt delivery is assumed at end+200 ns, after every
listed event; unavailable effect evidence is recorded at end+300 ns. All presses are
before end. Release may be before end bookkeeping or after the recorded action phase.
The finite one-press domain includes both orders for each press/release tie.

The projected request, command, manifest, lease and surface identities are fixed.
Alternative histories are possible worlds for that same projected command; using the
same synthetic receipt identifier across worlds does not mean two executions were
accepted in one lifecycle or that command reuse was tested. A digest or opaque ID is
not, by itself, an authenticated reconstruction of the missing event order.

This snapshot model intentionally does not assume a terminal-release promise from the
backend. An honest backend with a stronger guarantee may make the problematic world
unreachable. The selected kernel README already states that its start lower bound
does not prove release after the final action or physical input state. The construction
characterizes that residual rather than overturning the existing lower-bound repair.

The initial ordinary literal checks used source main `6da2b492b9c2a9d76e5c54d35a0ae50b7b49edde`.
Before the primary freeze, #6859 advanced main. All four original construction source
files remain under `construction_sources/`; `__init__`, contracts and lifecycle are
byte-identical between the two bases. Only `BackendRegistry.create` changed, and that
method is never invoked here. The primary source was updated prospectively. Cases,
decision gates and comparison definitions were unchanged; no primary execution was
repeated. [SOURCE.json](SOURCE.json) records the source change and reuse boundary.

## Actual first outcomes

| Predicate or comparison | Observed result | Interpretation |
|---|---:|---|
| Complete frozen histories | 36 | Exhaustive for the declared finite domain, not a workload sample |
| Distinct complete receipt projections | 10 | Two end values × five release values |
| Projections admitting both final states | 6 | Interior release values at both end values |
| Actual kernel `release_verified` | true on all 36 | Reports the supplied verified-empty release |
| Kernel report differing from terminal-empty truth | 12 | Conditional mismatch in this snapshot model, not a real-backend failure count |
| `R >= E` accepts a modeled held final state | 0 | No press occurs at or after E in this domain |
| `R >= E` refuses a modeled empty final state | 12 | Safe release before end bookkeeping is refused |
| Complete ordered witness differs from final-state truth | 0 | Consumes extra complete event-order information |
| Separate raw-only integrity audit | PASS | Reconstructs rows, projection, outcome, comparisons and prospective counts |
| Effective copied-raw corruptions refused | 12/12 | Each turns an intact PASS into HOLD |
| Scientific model decision | FAIL_TERMINAL_RELEASE_IDENTIFIABILITY | At least one intact opposite-truth projection class exists |

The six mixed classes have four histories each; the other four classes have three
each. These counts are descriptive properties of a chosen domain, not failure rates,
probabilities, effect estimates or empirical performance measurements. `release_verified`
is compared with a stronger terminal-empty predicate explicitly; the report does not
silently redefine the product field's point-in-time meaning.

Candidate: `2026-10-03T03:16:18.748814+00:00` to
`2026-10-03T03:16:18.911178+00:00`, exit 0. Separate auditor:
`2026-10-03T03:16:18.992180+00:00` to
`2026-10-03T03:16:19.171759+00:00`, exit 0. One invocation each, zero retries, no
timeout. These capture endpoints establish execution/provenance, not benchmark results.
The first raw and audit are preserved in [run01/raw.json](run01/raw.json) and
[run01/audit.json](run01/audit.json); full public stream/receipt derivations are retained.

## A minimal collision and proof

Both raw rows below have start 100 ns, end 700 ns and release snapshot 400 ns, with
every `ExecutionReceipt` field equal after type-sensitive canonical JSON serialization.
The command has one modeled press. The delivered release says verified true with no
keys or buttons down; both actual kernel outcomes have `release_verified=true` and
`effect_verified=false`, stage/reason `unavailable`.

| Original case ID | Modeled input order | Terminal A | End floor | Ordered witness |
|---|---|---|---|---|
| `e700-p200-r400-time` | start 100 → press 200 → release 400 → end 700 | up | false | true |
| `e700-p600-r400-time` | start 100 → release 400 → press 600 → end 700 | held | false | false |

Let `p(h)` be the full aggregate receipt projection of a history, `t(h)` its final
empty-input truth, and `f` any receipt-only deterministic decision. These retained
histories satisfy `p(h1) = p(h2)` and `t(h1) != t(h2)`. Therefore
`f(p(h1)) = f(p(h2))`; it cannot equal both truths. A randomized decision given the
same projection likewise cannot guarantee both different truths. This argument needs
only the collision, not all 36 rows or an estimated distribution.

| 記号 | 日本語の意味・定義 | SI 単位 | 範囲・前提 | 型 |
|---|---|---|---|---|
| h, h1, h2 | 完全な modeled event 履歴。h1/h2 は上記の異なる最終状態の対 | 非物理の記録（SI 単位なし） | 固定36履歴、外部・未記録入力なし | event record の有限列 |
| p | 履歴から kernel へ届ける完全な ExecutionReceipt projection を取る写像 | 非物理の写像（SI 単位なし） | 全フィールド・JSON scalar 型を保持、key 順序のみ正規化 | 履歴 → typed JSON record の関数 |
| t | 履歴の最終入力が空かを表す真理値 | 1（無次元） | 完全な1-key event 列から導く | 履歴 → Boolean の関数 |
| f | レシートだけから最終入力が空かを決める決定規則 | 出力は 1（無次元） | p 以外の event/provenance 情報を受け取らない | typed JSON record → Boolean の関数 |

時刻・event 順序の記号 S/E/P/R/j/K は [PLAN.md](PLAN.md) の日本語変数表で定義する。
上の等式は同一 typed projection と Boolean の比較であり、異なる時計や単位の量を比較しない。

At equal timestamps, explicit event order still matters. In the raw pair
`e700-p400-r400-press-release` and `e700-p400-r400-release-press`, an identical 400 ns
press/release timestamp produces up versus held. A proposed last-action timestamp
field alone would still need a tie-order convention or a stronger serialization
guarantee; this assay does not choose or authenticate that future contract.

The end floor is a strong simple conservative alternative for this domain: all
`R >= E` histories are safe because P < E. It discards the safe first row and 11 other
safe interior-release histories. This is why the present evidence does not justify
changing the runtime lower bound to `ended_ns` as an unconditional repair. A complete
sequence witness can distinguish the rows because it supplies the missing information;
its agreement is not an equal-information efficacy/performance comparison. No privileged
trace state is made available to a controller by this research package.

## Integrity, preservation and inspection limits

Freeze commit `676187138bad090909ac8ad87fd48cc2620690c4` preceded the primary commands.
[FREEZE.json](FREEZE.json) was created at `2026-10-03T03:16:16.107586+00:00`, fixes
18 inputs, and has SHA256
`82107800e25c47b2929dc587fd21b2f489d508ef11ea0bbee6a43bc01f17f2df`.
The raw is 61,137 bytes, SHA256
`ca6ffaaba7f9b57c8c53b648eed8d290fe8eca146db469297864638b777c6e95`.
The audit is 4,828 bytes, SHA256
`f25f8a844c2499450e1ee0d656d837fd80d9ef2fbbef0650c3f18d260ea22a89`.

The separate auditor imports neither candidate nor kernel. Its independently authored
Boolean reducer validates exact event types/census/order, reconstructs terminal state,
snapshot, full typed projection, source/hash joins, actual expected outcome and both
comparators. Copied-raw controls cover Boolean/number projection aliases, outcome and
comparison flips, nonempty release snapshot, flipped terminal state, missing events,
Boolean sequence, duplicate rows, wrong freeze and an extra projection field. Controls
do not rewrite or rerun original raw. Prospective count disagreements retain HOLD.

The ordinary pre-freeze construction ran five methods, including three isolated
literal candidate row constructions, and passed. Its module was later renamed
byte-for-byte from `test_construction` to `construction_checks` to avoid automatic
archive test discovery. The original command and outcomes remain retained. The first
sparse-worktree setup problem is also disclosed, including its truncated diagnostic
limit, in [SETUP_NOTES.md](SETUP_NOTES.md).

A post-run read-only inspection at `03:24:36`–`03:24:39` UTC checked all 18 working
inputs against both their freeze pins and actual prospective Git bytes, four primary
and four earlier construction source blobs against their source commits, all three
original capture receipts/stream pairs against disclosed public derivations, and nine
Python sources by syntax parsing only. It did not import or execute candidate, auditor
or kernel. See [run01/readback.json](run01/readback.json). Public interpreter/cwd
placeholders and omission of pid are explicit; actual original captures stay private
with separate hashes. This verifies retained bytes on the author's host rather than
authenticating backend provenance or supplying independent worker approval.

The manifest covers final published files except itself. Additional readback/report
sources were written after execution and are not represented as prospective inputs.
Later finite Git/tree inspections and their diagnostic limits are separately described
in [POSTRUN_NOTES.md](POSTRUN_NOTES.md). No claimed all-tests-green result is inferred
from the scoped checks or from another worker's test runs.

## Remaining work before an integrated claim

This result is limited to a complete, sequential, one-key, common-clock synthetic
snapshot model. It does not cover operating backends, application effects, multiple
keys/buttons, external actors, ownership transitions, cross-clock conversion, scheduler
timing, authenticated logging, concurrency, MAP01, latency, tokens or model success.
`EffectStatus.UNAVAILABLE` deliberately avoids an application-effect verification claim.

The remaining empirical/product question is which existing backend contract guarantees
that release is terminal and which public, complete evidence can verify that guarantee
without introducing unnecessary model calls or waits. Any eventual event witness needs
explicit coverage, identity, ordering, completeness and provenance; any end timestamp
rule needs an actual end-semantics contract. No runtime/API/workflow/promotion change is
part of this evidence package. Existing scientific allocations and original outcomes
are unchanged. FINAL-v5 assigned content votes, a nonauthor exact-current-main combination
check, actual GitHub conditions and one conditional history-preserving application remain
separate from this author's analytical and byte-inspection evidence.
