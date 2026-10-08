# Agent Interface — Research Convergence / Freeze Proposal

現在のAgent Interface研究は、改善案を追加し続けるだけだと終了条件がなくなる。

この研究では、

> **「改善案がなくなったら終了」ではなく、「研究対象の構造が収束したらarchitecture discovery phaseを終了する」**

という停止基準を導入したい。

目的は、どこまでも局所改善を続けるのではなく、

* 新しいfailure modeがまだ頻繁に見つかっているのか
* architecture変更がまだ大きいのか
* 改善の限界効用が下がってきたのか
* 新しい変更が既存機能を壊さなくなってきたのか

を継続的に記録し、研究が十分成熟した時点でcore semanticsをfreezeすること。

---

## 1. Evolution Ledgerを作る

今後の主要実験・revisionごとに、最低限以下を記録する。

推奨：

```text
research/evolution.csv
```

例：

```text
revision
date
hypothesis
mechanism_added
apps/environments
episodes
success_rate
hard_success_rate
new_failure_classes
known_failure_recurrences
regressions
p50
p95
p99
planner_boundaries
observations
serialization_bytes
actual_tokens_if_available
architecture_changes
decision
notes
```

Decisionは例えば：

```text
PASS
HOLD
REJECT
PROMOTED
DEPRECATED
```

とする。

既存のhistorical experimentsも可能な範囲でbackfillする。

---

## 2. Failure taxonomyを作る

単純な「バグ件数」ではなく、

> **新しいfailure classが何種類見つかったか**

を管理する。

例えば現時点で想定できるカテゴリ：

```text
input delivery failure
input ownership failure
expiry / lease failure
wrong-target / focus validity failure
stale action failure
observation freshness failure
critical-event loss
transport/reconstruction failure
binding lifetime failure
route invalidation failure
modal/state transition failure
capture/context skew
motor-control failure
planner-boundary failure
recovery failure
```

必要に応じて追加する。

重要：

同じfailureが100回出ても、

```text
new_failure_classes = 0
known_failure_recurrences = 100
```

として区別する。

---

## 3. Failure Discovery Curve

横軸：

```text
累積実験量
または
revision number
```

縦軸：

```text
new failure classes discovered
```

を記録・可視化する。

理想的には、

```text
10
7
5
3
2
1
0
0
0
```

のように減っていく。

この曲線が下がることは、

> **Agent–Computer controlに存在する未知のfailure構造をだんだん理解できている**

ことを示す。

---

## 4. Regression Curve

新しい改善を導入した際に、

> 以前成功していた性質を何個壊したか

を記録する。

例：

```text
expiry追加
→ ordinary inputを壊した

focus guard追加
→ observe-only recoveryを壊した

subscription追加
→ event duplicate処理を壊した
```

各revisionについて、

```text
regressions_count
regression_classes
```

を保存する。

Architectureが成熟すれば、

```text
regressions / revision
```

は0付近へ収束するはず。

---

## 5. Architecture Churn Curve

各revisionで、

```text
new primitive
removed primitive
protocol semantic change
state-model change
runtime ownership change
error-semantics change
```

など、core architectureをどれだけ変更したかを記録する。

単なるコード行数ではなく、

> **意味論が何個変わったか**

を見る。

例：

```text
architecture_churn_score
0 = implementation-only
1 = minor semantics
2 = local subsystem semantics
3 = core protocol/runtime semantics
```

などでもよい。

これが長期的に下がれば、

```text
「実装を改善している」
```

状態へ移行していて、

```text
「architecture自体を発見している」
```

フェーズを抜けつつあると判断できる。

---

## 6. Marginal Improvement Curve

各promotion candidateについて、

```text
success
p95/p99
planner boundaries
observation count
observed pixels
actual tokens
serialization bytes
recovery cost
wrong-target actions
stale actions
```

がbaselineに対して何%改善したか記録する。

特に、

```text
best meaningful improvement per revision
```

を追跡する。

例：

```text
R10  31%
R11  18%
R12  11%
R13   6%
R14   2%
R15   0.8%
```

のように下がるなら、現在のarchitecture上での限界効用が小さくなっている。

ただしcorrectnessは常にhard gateとする。

---

## 7. Research Freeze Candidateの条件

以下が一定期間同時に成立したら、

```text
Research Freeze Candidate
```

とする。

### Failure discovery

fresh/stress evaluationを十分回しても、

```text
new failure class ≈ 0
```

が複数revision継続する。

### Regression

新しい改善によるregressionが、

```text
≈ 0
```

に近づく。

### Architecture churn

core protocol/runtime semanticsの変更が減り、

```text
implementation tuning
backend work
performance tuning
```

が中心になる。

### Marginal gains

新candidateがpromotion thresholdを超えなくなる。

例えば通常、

```text
>= 10% meaningful improvement
```

をpromotion基準としているなら、

複数revisionにわたってこれを超える新しいarchitecture candidateが出なくなる。

### Cross-domain coverage

少なくとも性質の異なる複数環境で同じcore semanticsが成立する。

例：

```text
terminal / text
browser
spreadsheet
graphics/editor
multi-window/modal
continuous motor control
real-time environment such as DOOM
```

DOOM単独ではfreeze判断しない。

### Correctness stability

fresh/hidden/stressで、

```text
success
wrong-target input
stale action
held-input cleanup
critical-event handling
```

が安定する。

---

## 8. Freezeの意味

Research Freezeは、

> 「Agent Interfaceは完全で、今後改善不要」

という意味ではない。

意味は、

> **core architecture discoveryは一旦終了し、以降は主にengineering / portability / productizationへ移る**

ということ。

フェーズを明確に分ける。

```text
Phase A
Architecture Discovery

↓ Research Freeze

Phase B
Runtime Consolidation

↓ Protocol Freeze

Phase C
Windows / macOS backend

↓ Cross-platform validation

Phase D
Production stabilization
```

---

## 9. Linuxフェーズの終了条件

現在Linux/X11で探索しているため、

OS移植開始の条件も定義しておく。

Windows/macOS移植へ進んでよい条件：

```text
core input authority semantics stable
lease / expiry stable
cancel / release stable
focus/window validity model stable
observation/event semantics stable
stale-action semantics stable
universal input ISA mostly stable
planner/runtime boundary mostly stable
```

この時点で、

```text
X11-specific code
```

と、

```text
OS-independent semantics
```

が明確に分離できている必要がある。

---

## 10. 推奨グラフ

最低限以下を自動生成する。

```text
1. cumulative new failure classes
2. new failure classes / revision
3. regressions / revision
4. architecture churn / revision
5. best marginal gain / revision
6. success / revision
7. p95 / p99 latency
8. planner boundaries / successful task
9. observations / successful task
10. wrong-target / stale-action incidents
```

可能なら同一figureへ詰め込みすぎず、個別chartで保存する。

---

## 11. 推奨ファイル構成

```text
research/
  evolution/
    evolution.csv
    failure_taxonomy.md
    freeze_criteria.md
    generate_curves.py
    charts/
      failure_discovery.png
      regression.png
      architecture_churn.png
      marginal_gain.png
      success.png
```

既存experimentのraw resultは移動しない。

Evolution Ledgerは既存研究へのindexとして使う。

---

## 12. Decision rule

今後、新しい研究アイデアが出た時は、

「できるから試す」

ではなく、

以下を確認する。

```text
1. 未解決failure classを潰すのか
2. core architecture uncertaintyを減らすのか
3. 主要metricをpromotion threshold以上改善しうるか
4. cross-domain generalityを検証するのか
```

どれにも該当しない場合は、

```text
DEFER
```

を許容する。

これにより研究が無限に拡散するのを防ぐ。

---

# 最終提案

この研究の終了条件を、

> **「改善案が尽きること」**

ではなく、

```text
failure discovery → 0
regression → 0
architecture churn → 0
marginal gain → small
cross-domain correctness → stable
```

の同時収束として定義する。

これが成立した時点で、

> **Agent Interface architecture discovery phase complete**

と宣言し、core semanticsをfreezeする。

その後はWindows/macOS対応、runtime consolidation、performance engineering、distributionへ移行する。

この収束記録自体も、Agent Interface研究の重要な成果物として残す。
