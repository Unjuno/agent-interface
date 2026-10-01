# Frozen plan

Issue #944. Standard-library only. One deterministic invocation.

- Period: `round(1e9/35)` ns.
- Attempts: 3; immediate retry; no deliberate gap.
- Grid: 1 us.
- Frozen spans: 10 ms, 18 ms, floor(2T/3), ceil(2T/3)+1 us, 20 ms, 25 ms, T.
- Independent methods: direct attempt simulation and circular interval intersection.
- Two-attempt control at floor(T/2) and +1 ns.
- Invalid span controls: 0, -1.
- No post-result source/threshold/schedule changes.
