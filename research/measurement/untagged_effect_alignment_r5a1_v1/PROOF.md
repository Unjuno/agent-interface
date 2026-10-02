# Complete ordered-subsequence argument

## Variables
| Symbol | Meaning (日本語) | SI unit | Definition / domain | Type |
|---|---|---|---|---|
| n | 送信要求数 | 1 | positive integer, implementation1..32 | scalar integer |
| k | 封印された効果通知数 | 1 | integer0..n | scalar integer |
| j | 効果の通番 | 1 | integer1..k | scalar integer |
| i | 候補となる要求通番 | 1 | integer1..n | scalar integer |
| f | 効果から要求への対応 | 1 | strictly increasing injection from1..k to1..n | function |
| S_j | j番目効果の可能な起点集合 | 1 | all f(j) over admissible f | set of integers |

Assume closed, complete order-preserving effects, at most one per request and no other effects.
Necessity: j-1 earlier effects require j-1 distinct earlier requests, hence f(j)>=j.
The k-j later effects require k-j later requests, hence n-f(j)>=k-j, or f(j)<=n-k+j.
Sufficiency: for any integer i within these bounds, choose the first j-1 request indices
1,...,j-1; then i; then i+1,...,i+k-j. They are in1..n, strictly increasing, and map
effect j to i. Empty prefix/suffix are permitted. Therefore
S_j={j,j+1,...,n-k+j}. Its cardinality is n-k+1. For k>0 a unique origin exists iff k=n.
For k=0 there are no effect-origin queries; this does not prove inputs were not executed.
Units: all quantities are event counts (dimension1); integer differences and bounds are
commensurate, not seconds or physical positions.
Example: n=3,k=2 gives S_1={1,2},S_2={2,3}; the original effective subsets {1,2},{1,3},{2,3}
produce identical untagged notifications. No deterministic single-origin answer can be correct
in all three worlds. Independent oracle enumerates all combinations rather than using bounds.

Out-of-contract: n=k=2 with effects arriving from request2 then request1 violates order.
The ordered formula returns singleton1 then2, which is wrong for this unobservable reversal.
Thus supplying an unjustified ordered=true assertion does not authenticate causality. The live
study only establishes the declared cooperative, synchronous contract, not arbitrary GUI order.
