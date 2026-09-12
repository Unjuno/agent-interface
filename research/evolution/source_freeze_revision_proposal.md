# Research Freeze Criteria Revision Proposal

## 目的

現在のResearch Freeze基準では、

> 単一の新architecture candidateが、事前に設定したmeaningful improvement threshold（暫定10%）を超えなくなった

ことを、収束判断の一要素としている。

この考え方自体は、個別candidateのpromotion判断には有用である。

ただし、

> **Research Freezeの終了条件として「単発10%」を使うのは早すぎる可能性がある。**

理由は、小さい独立改善が複数存在する場合、それらは累積すると大きな差になるためである。

---

## 1. 小さい改善は無視できない

例えばコスト削減が毎回独立して8%得られる場合、

```text
0.92^5 ≈ 0.659
```

なので、5つ組み合わせると約34%削減になる。

同様に、5%削減を10回積み重ねると、

```text
0.95^10 ≈ 0.599
```

となり、約40%削減になる。

throughputを毎回10%改善できるなら、

```text
1.10^5 ≈ 1.61
```

なので、5段階で約61%向上する。

したがって、

```text
candidate A: 6%
candidate B: 5%
candidate C: 4%
```

をすべて

> 「10%未満なので重要ではない」

として捨てると、実際には15%前後以上の改善余地を失う可能性がある。

---

# 2. Promotion ThresholdとFreeze Thresholdを分離する

以下を明確に分けるべきである。

## Candidate Promotion

単一candidateをcoreへ採用するかどうか。

ここでは例えば、

```text
>= 10% improvement
```

を強いpromotion signalとして残してよい。

ただし10%未満でも、

* correctnessを維持
* regressionなし
* implementation complexityが小さい
* 別のbottleneckへ独立して作用する
* cross-domainで再現する

のであれば、候補として保持する価値がある。

---

## Research Freeze

architecture discoveryを終了するかどうか。

こちらは、

> **単一candidateの最大改善率**

ではなく、

> **残っている合理的な改善候補を組み合わせた時に、Pareto frontierがどの程度まだ動くか**

で判断する方がよい。

---

# 3. Individual GainだけでなくBundle Gainを測る

今後のEvolution Ledgerでは、可能なら以下を区別する。

```text
individual_gain
combined_gain
interaction_gain
complexity_cost
```

例えば、

```text
Observation Subscription      6%
Control Codec                 5%
Planner-boundary reduction    8%
Input scheduling              4%
```

という結果が出た場合、

単純な合計を23%とはしない。

実際に組み合わせたcandidate bundleを測る。

理由は、

* 同じbottleneckを削っているため効果が重複する場合
* 一方の改善がもう一方の効果を増幅する場合
* complexityやregressionによってnet gainが減る場合

があるため。

---

# 4. Interaction Gainを明示する

候補AとBについて、

```text
gain(A)
gain(B)
gain(A+B)
```

を可能な範囲で測る。

例えば、

```text
A = 6%
B = 5%
A+B = 10.7%
```

ならほぼ独立。

一方、

```text
A = 6%
B = 5%
A+B = 6.8%
```

ならかなり重複している。

逆に、

```text
A = 6%
B = 5%
A+B = 15%
```

なら相乗効果がある。

この違いを無視して単一candidate thresholdだけを見るべきではない。

---

# 5. Freeze判断にはPareto Frontierを使う

Agent Interfaceでは単一metricだけで最適化できない。

重要な軸には、

```text
task correctness
wrong-target input
stale input
planner boundaries
end-to-end latency
p95 / p99
model tokens
observations
recovery cost
implementation complexity
```

がある。

そのためResearch Freezeは、

> **新しいreasonable candidateまたはcandidate bundleを追加しても、correctnessを維持したままPareto frontierがほとんど改善しなくなる**

ことを中心に判断する。

---

# 6. 改訂したFreeze条件案

以下が複数revisionにわたって同時に成立した時に、

```text
Research Freeze Candidate
```

を検討する。

### A. Failure discoveryが収束

```text
new failure classes ≈ 0
```

が十分なfresh/stress coverageで続く。

---

### B. Regressionが収束

```text
new regressions ≈ 0
```

または既知の小規模なものだけになる。

---

### C. Architecture churnが収束

core protocol/runtime semanticsの変更がほぼなくなり、

```text
backend work
implementation tuning
performance engineering
```

が中心になる。

---

### D. Individual marginal gainが縮小

単一candidateの改善が徐々に小さくなる。

ただしこれは補助指標とし、単独ではFreeze理由にしない。

---

### E. Bundle marginal gainも縮小

直近の合理的なcandidate群を組み合わせても、

```text
net improvement
```

が小さい。

例えば、

```text
single best: 4%
candidate bundle: 6%
```

程度しかfrontierが動かず、

しかもそのために大きなcomplexityやriskが必要なら、収束の強い証拠になる。

逆に、

```text
single candidates:
6%
5%
4%

combined:
18%
```

なら、単発10%未満でも研究はまだ全く終了していない。

---

# 7. 「10%」の扱いを変更する

現在の10%を完全に削除する必要はない。

推奨する扱いは、

```text
10% = strong individual promotion threshold
```

であり、

```text
10% = research freeze threshold
```

ではない。

Research Freezeでは、

```text
remaining plausible cumulative gain
```

を見る。

---

# 8. Complexity Costも評価する

1%改善を得るためにcore semanticsが大きく複雑化するなら、採用価値は低い。

逆に、3%改善でも数行のdeterministic optimizationで、

* regressionなし
* portabilityへの悪影響なし
* maintenance costほぼなし

なら採用価値は高い。

したがって実質的には、

```text
net research value
=
performance/correctness gain
-
complexity cost
-
regression risk
-
portability cost
```

を見るべきである。

厳密な一つの数値にする必要はないが、判断項目として明示する。

---

# 9. Evolution Ledgerへの追加候補

可能なら以下を追加する。

```text
individual_gain
bundle_id
bundle_gain
interaction_effect
complexity_delta
new_core_semantics
net_decision
```

例：

| candidate          | individual | bundle | complexity | decision          |
| ------------------ | ---------: | -----: | ---------: | ----------------- |
| Subscription       |         6% |        |        low | retain            |
| Codec              |         4% |        |        low | retain            |
| Boundary reduction |         8% |        |     medium | retain            |
| Bundle S+C+B       |          — |    16% |     medium | continue research |

---

# 10. 改訂後のResearch Freezeの考え方

旧：

> 10%以上改善するcandidateが出なくなったら収束。

改訂案：

> **新しいfailure class、regression、core semantic changeがほぼ収束し、さらに残っている合理的な独立candidateを複数組み合わせても、correctnessを維持したPareto frontierを意味のある量だけ動かせなくなった時にResearch Freezeを検討する。**

---

# 11. 最終提案

Research Freeze判断では、以下の4本を同時に見る。

```text
failure discovery        → 0
regression               → 0
architecture churn       → 0
remaining bundle gain    → small
```

さらにcross-domain correctnessが安定していることをhard gateとする。

重要なのは、

> **「単発の改善が小さくなった」ことではなく、「まだ残っている改善を合理的に束ねても大きな差が出なくなった」こと。**

これをarchitecture discovery phaseの終了条件とする方が、Agent Interfaceのように多数の小さな最適化が積み重なるシステムには適している。
