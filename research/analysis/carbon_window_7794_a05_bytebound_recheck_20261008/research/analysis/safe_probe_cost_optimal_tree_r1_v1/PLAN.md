# Safe-probe cumulative-cost optimal tree R1

Parent #1716; predecessor #1836.

H: for deterministic hypotheses and positive-cost explicitly safe probes, exact no-prior identification minimizes worst-case cumulative probe cost by Bellman recurrence C(V)=min_p[c_p+max_o C(V_p,o)], with unsafe/nondiscriminating probes excluded and IMPOSSIBLE when no safe separating tree exists.

T: candidate bitmask DP vs independent frozenset decision-tree oracle. Exhaustive n=2..4, two binary probes, all output maps/safe flags/costs1..3 =12,096 cases. Formal adds100,000 deterministic random instances. Compare exact optimal cost/first probe, IMPOSSIBLE, unsafe use, label invariance, and recursive #1836-style greedy cumulative cost.

D: candidate/oracle mismatch0; unsafe selection0; IMPOSSIBLE mismatch0; label-permutation changes0; greedy-cost-suboptimal>0; directed cost10 perfect probe vs two cost1 binary probes gives optimal2/greedy10; independent audit/corruption/source integrity PASS; formal1/reruns0.

C: deterministic exact identification, positive additive costs, worst-case objective only. No stochastic outputs, state-changing/reversible probes, calibrated priors or real GUI safety.

U: analytical decision-tree semantics only; no runtime/model/latency/product claim.
