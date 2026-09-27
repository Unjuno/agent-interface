# Issue #4279 — cyclic semantic truth-maintenance

Allocation: `semantic-truth-cycle-4279-20260923-01`
Base main: `c79f70a93d603748b155449016581dd7b9aac205`

## H
A cached local-support evaluator can preserve a self-justifying TRUE cycle after the last externally grounded support disappears. An SCC-grounded retraction policy that only accepts finite derivations rooted in current base facts should retract the affected cyclic component, preserve unrelated derived facts, and restore the component when a fresh external anchor returns.

## T
Standard-library deterministic fixture only. Base facts: anchor, gate, unrelated. Derived facts A/B/C/D with support sets A<-anchor OR B; B<-A; C<-B AND gate; D<-unrelated. Compare LOCAL_SUPPORT_RETAIN versus SCC_GROUNDED_RETRACT over the frozen 12-step schedule in schedule.py. Candidate recomputes only descendants of changed base facts but grounds the values against a least fixed point from current base evidence. One formal invocation after public source/hash freeze. No retries/replacements/tuning.

## D
PASS_CYCLIC_TRUTH_RETRACTION_SCOPED requires: 12 rows; candidate equals independent finite-proof oracle at every row; unsupported candidate TRUE=0; A/B/C not TRUE after ANCHOR_FALSE, ANCHOR_UNKNOWN, ANCHOR_FALSE_AGAIN; fresh anchor restoration rederives correctly; unrelated-only changes never include A/B/C in affected region; D follows only unrelated; candidate recomputations < global 48; naive comparator exposes at least two stale TRUE witnesses; macro-ready equals oracle; authority none; independent audit errors=[]; all 12 frozen corruption controls reject; source hashes unchanged postformal.

Any unsupported candidate TRUE => FAIL_UNSUPPORTED_CYCLE_RETENTION. Missing source/process/raw/audit evidence => STOP/HOLD.

## C
Finite authored positive-support graph. Complete support declarations are assumed. SCC-aware grounding is one implementation of finite-proof semantics; equivalent algorithms may exist. Directed schedule is not a natural frequency estimate.

## U
No arbitrary negation cycles, weighted/confidence support, hidden neural dependencies, cross-process persistence, crash durability, GUI/input/model/provider, task effect, token/latency benefit, production authority or global roadmap completion.
