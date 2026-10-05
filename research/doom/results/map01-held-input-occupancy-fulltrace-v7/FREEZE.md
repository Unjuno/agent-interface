# Full-trace held-input occupancy v7 — freeze

Base: origin/main `a5f2bf291787000627abbc12c123af4bd2873d5c`.
Worktree branch: `research/issue59-early-release-boundary-v1-20261004`.
Type: deterministic CPU-only posthoc boundary successor; no model, GUI, game, input, Docker, or live allocation.

## H / T / D / C / U

**H.** If a normally completed hold contains a same-program verified empty-input release before its final post-release observation, v4 can overstate its lower-bound occupancy. V7 must stop the confirmed interval at the latest in-loop capture before that release and stop the upper envelope at the verified release.

**T.** A synthetic boundary first failed against v4: key ACK 12 ms, in-loop capture 30 ms, verified empty release 40 ms, later capture 80 ms, post-release capture 90 ms. V7 requires 30 ms confirmed-until, 40 ms release endpoint, and 18–29 ms occupancy. Then run v7 once on each immutable v38/v39 trace and run its separate raw auditor once on both outputs.

**D.** PASS only if the synthetic boundary passes; every started hold in both traces appears exactly once; source hashes match; independent audit has zero errors; and existing v4 results are unchanged. Otherwise retain FAIL/STOP without retry.

**C.** This synthetic failure may not affect retained totals if neither trace contains a completed-hold early release.

**U.** No exact ordinary key-up timestamp, task-effect, recovery, performance, causal, matched-tempo, or product claim. Two stochastic source episodes only.

## Preserved v6 construction STOP

The immediately preceding v6 candidate was invoked once on each trace and both commands exited 1 before output creation due to a decision-helper namespace error. The failed version and details remain in `map01-held-input-occupancy-fulltrace-v6/STOP_V6.md`; v7 has a new source identity and output path.

## Frozen SHA-256 inputs

- `research/doom/analyze_map01_held_input_occupancy_fulltrace_v7.py`: `8b1b1dfa1e9da053ce5be7b3acd8e5dbc1d5ee99fe819767348988e3d8966bd1`
- `research/doom/audit_map01_held_input_occupancy_fulltrace_v7.py`: `511ddf60275d11125867d07b67a6c7080a48342addc3bf66cd8fcc28669598d3`
- `research/doom/test_map01_held_input_occupancy_fulltrace_v7.py`: `e19f47cb11142386fe934a3e5e0c5d01c94397967e5a642231201705b0f7be40`
- `research/doom/results/map01-held-input-occupancy-fulltrace-v4/v38.json`: `2aeec615483a754233c5b9d483be001952e7ca6cd66370bd1e90bf0389427eee`
- `research/doom/results/map01-held-input-occupancy-fulltrace-v4/v39.json`: `1cd61f82a2ff832131be4a448bc90663f01c4acaab278807a969d2ef24a3b889`
- `research/doom/results/map01-v38-integrated-threat-live-01/report.json`: `7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58`
- `research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl`: `80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3`
- `research/doom/results/map01-v39-coast-liveness-live-01/report.json`: `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`
- `research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl`: `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`

## One-shot commands

```sh
python3 research/doom/analyze_map01_held_input_occupancy_fulltrace_v7.py research/doom/results/map01-v38-integrated-threat-live-01 --out research/doom/results/map01-held-input-occupancy-fulltrace-v7/v38.json
python3 research/doom/analyze_map01_held_input_occupancy_fulltrace_v7.py research/doom/results/map01-v39-coast-liveness-live-01 --out research/doom/results/map01-held-input-occupancy-fulltrace-v7/v39.json
python3 research/doom/audit_map01_held_input_occupancy_fulltrace_v7.py --repo . --candidate-dir research/doom/results/map01-held-input-occupancy-fulltrace-v7 --out research/doom/results/map01-held-input-occupancy-fulltrace-v7/audit-v7.json
```
