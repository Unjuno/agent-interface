# #1860 Passive-trace identifiability of interface automata

TASK: `INTERFACE-AUTOMATON-PASSIVE-IDENTIFIABILITY-R0-20260919-001`

Parent #1657.

## H
For a deterministic stationary automaton with directly observed state/action labels and a declared finite state-action domain, passive evidence identifies the complete next-state table iff every declared state-action pair is observed at least once. If any pair is unobserved, at least two automata can agree on all observed evidence and differ only at that pair.

## T
Exact finite confirmation on 3 states ×2 actions:
- six transition-table entries;
- three possible next states per entry;
- all 3^6=729 automata;
- all 2^6=64 coverage masks;
- group automata by observed transition signature for each mask;
- require exactly 3^k signature classes, each of size 3^(6-k), where k is observed-pair count;
- retain explicit one-missing-pair ambiguity witness;
- independent auditor recomputes all group sizes;
- corruption controls reject k=5 uniqueness, observed-transition mutation without signature change, unobserved-impossible claim, and altered universe counts.

## D
PASS iff automata729, masks64, every class-size formula exact, every incomplete mask remains ambiguous, full coverage yields singleton classes, explicit ambiguity witness exists, independent audit and corruption controls pass, formal1/reruns0/replacements0/tuning0.

## C
Hidden/aliased states, nondeterminism, stochastic transitions, abstraction errors, reachability/reset constraints, structural priors and partial action observability are outside this model.

## U / stop
Identifiability theorem only. No learner/sample-efficiency/active-probe/live-GUI/model/product claim. Stop after first deterministic result and audit.
