# Typed effect observation recorded-start consistency

Existing parent #5215; engineering repair, FINAL-v5. Existing #5156/root source author.
Branch fix/kernel-effect-start-5156-20261003. No shared checkout or main change.

H: the current typed lifecycle accepts a matching effect observation earlier than
its already accepted execution receipt's recorded start. The proposed minimum
consistency boundary refuses that relation before effect/stage mutation. It
preserves equality, during-execution observations, late delivery, identity
refusals, effect occurrence, release evidence and subsequent valid recovery.

T: first execute the six literal regression methods against exact unmodified
source. Expected first outcome is eleven missing-ContractError failures, with
the valid/identity controls passing. Only after retaining that first output,
make the smallest local source correction and run the focused tests and current
kernel directory discovery normally and optimized. Snapshot original source and
preserve exact source/test/helper/argv/UTC/exits/streams. A separately frozen
ordinary finite construction matrix and raw-only auditor may strengthen the
repair; they do not repeat the legacy #5216 matrix or any formal allocation.

D: require refusal of typed matching observations below the recorded start,
unchanged EXECUTED/request/execution/effect state after refusal, valid same-flow
recovery, exact equality/later controls, and no regression in the unchanged
neighboring guards. Setup errors are separate from an expected assertion RED.
Do not loosen the expected predicate or relabel any first failure.

C: comparing only accepted begin is weaker when recorded execution starts later.
Requiring observation at/after execution end would reject during-execution
controls and would choose a disputed legacy semantic policy. Expired authority
at delivery is not proof that an action exceeded its cutoff. A truthful common
monotonic caller can already supply sensible times; this boundary does not
authenticate or synchronize caller/backend clocks.

U: typed sequential API and explicitly comparable integer timestamps only.
This does not establish physical/task effects, observation freshness after the
last action, input release, no-input after an error, thread safety, security,
authenticated provenance, public MCP use of RequestLifecycle, or performance.
The public MCP path currently does not consume this lifecycle. Existing
#5216/#5225/#5229 evidence and HOLD remain unchanged. Existing nominal admission
#6875/#6923 and lost-receipt occurrence #6894 stay independently owned. No
effect-after-end or execution-end lease cutoff is adopted.

| 記号 | 日本語の意味・定義 | SI単位 | 範囲・前提 | 型 |
|---|---|---|---|---|
| A | 受理した begin の時刻 | ns（10^-9 s） | 本 fixture は400。同じ比較可能な時計 | 非負整数スカラー |
| S | 受理した実行レシートの started_ns | ns（10^-9 s） | 本 fixture は600、A以上 | 非負整数スカラー |
| F | 効果観測レシートの observed_ns | ns（10^-9 s） | 型付き観測。比較可能な時計 | 非負整数スカラー |
| E | 実行レシートの ended_ns | ns（10^-9 s） | 本 fixture は800、S以上 | 非負整数スカラー |
| L | lease の valid_until_ns | ns（10^-9 s） | 本 fixture は1000。delivery の上限に使わない | 正整数スカラー |

Minimum consistency is F >= S; equality remains allowed. This is a necessary
timestamp relation under the declared interpretation, not a sufficient semantic
postcondition. No probability or unmeasured latency benefit is asserted.

Resource cap: one small stdlib Python child at a time, 30 s per regression,
2 MiB per stdout/stderr capture and 8 MiB evidence target. No backend open,
native input, GUI, model/provider, network during checks, container/WSLc/GPU,
new worker or resource/apply lock. Common deadline is unknown, not extended.
