# Passive automaton identifiability R0 (Issue #1860)

Decision: PASS_PASSIVE_AUTOMATON_COVERAGE_IDENTIFIABILITY_SCOPED.

This additive analytical/container result tests a finite deterministic stationary automaton with 3 directly observed states and 2 directly observed actions. It enumerates all 3^6 = 729 transition tables and all 2^6 = 64 observation-coverage masks. For a mask with k observed state-action pairs, every observational equivalence class has size 3^(6-k); therefore the full table is identifiable exactly at k=6.

Scope is theorem confirmation only: no learning algorithm, active probing, GUI transfer, model quality, latency, or production ABI claim. Formal invocation=1, reruns=0, replacements=0, tuning=0.