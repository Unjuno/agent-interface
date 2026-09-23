# TEMPORAL-SPECULATION-PLANNER-GAP-RUNG1-20260918-001

H: Preserve Rung0 branch universe/K/selectors/admission; add one fixed 40 ms planner-unavailable interval. Temporal-informed preparation should lower realized-state -> independently verified effect latency because its fixed-K hit rate is higher.
T: 400k fresh deterministic cases reproducing the retained Rung0 aggregate distribution exactly (dynamic320k + ambiguous80k), plus 24 fresh subprocess discriminator cases. Fresh state appears at10 ms; hit local handling1 ms; miss/wait acts only after40 ms. Same exact-match/authority/expiry gate in every speculative arm.
D: PASS only if candidate/oracle match, temporal hit count exceeds current, wrong/stale/authority0, large-corpus mean temporal latency >=3 ms below current and >=10 ms below wait, and subprocess medians satisfy temporal<5 ms/current>=25 ms/wait>=25 ms with >=20 ms paired separation and independently logged effects. Otherwise retain HOLD/FAIL exactly.
C: +8.084pp hit-rate gain may be too small to exceed the preregistered mean-latency threshold at a 40 ms gap; a trivial velocity feature may be sufficient.
U: synthetic/controlled subprocess planner gap only; no frontier/model/task/MAP01 claim.
