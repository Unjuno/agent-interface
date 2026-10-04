# Full-trace held-input occupancy v6 — freeze

Base: origin/main `a5f2bf291787000627abbc12c123af4bd2873d5c`.
Worktree branch: `research/issue59-early-release-boundary-v1-20261004`.
Type: deterministic CPU-only posthoc boundary successor; no model, GUI, game, input, Docker, or live allocation.

## H / T / D / C / U

**H.** When a normally completed hold has a same-program verified empty-input release before its final post-release observation, the current lower bound can overstate occupancy. A successor that caps the bound at the last in-loop capture before that release will preserve existing v38/v39 results if neither has such a completed-hold release.

**T.** First reproduce the failure with a synthetic completed hold (verified release at 40 ms, preceding in-loop capture at 30 ms, later captures at 80/90 ms); freeze v6 candidate, raw-only auditor, tests, and immutable v38/v39 source hashes; apply candidate once to each trace; audit once using a separate raw reconstruction.

**D.** PASS only if the synthetic boundary yields confirmed-until 30 ms, release upper endpoint 40 ms, and occupancy [18, 29] ms; both immutable traces are reconstructed exactly once per started hold; source hashes match; the independent auditor reports zero errors; and no prior v4 output changes. Otherwise retain FAIL/STOP without retry.

**C.** The v4/v5 logic may still be correct for all current retained rows if no completed hold has an earlier verified release. A synthetic counterexample alone does not imply the historical aggregate is wrong.

**U.** This is a method boundary check over two existing stochastic episodes. It does not supply exact normal key-up time, semantic task effect, recovery efficacy, matched performance, causality, or product evidence.

## Frozen SHA-256 inputs

- `research/doom/analyze_map01_held_input_occupancy_fulltrace_v6.py`: `6e1a3c13e869fed698fd4ff08b8b14721d8604b673953372f9be7c2b13927fc3`
- `research/doom/audit_map01_held_input_occupancy_fulltrace_v6.py`: `7c2a9a044ccf0b9a12a60ce85dead449996e770fcb7e5d83b71ea87503f22b66`
- `research/doom/test_map01_held_input_occupancy_fulltrace_v6.py`: `a9669ec3d1026844abe105ad7d4bc1779730fecebb40b5b9b7dcb8346d21af1f`
- `research/doom/results/map01-held-input-occupancy-fulltrace-v4/v38.json`: `2aeec615483a754233c5b9d483be001952e7ca6cd66370bd1e90bf0389427eee`
- `research/doom/results/map01-held-input-occupancy-fulltrace-v4/v39.json`: `1cd61f82a2ff832131be4a448bc90663f01c4acaab278807a969d2ef24a3b889`
- `research/doom/results/map01-v38-integrated-threat-live-01/report.json`: `7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58`
- `research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl`: `80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3`
- `research/doom/results/map01-v39-coast-liveness-live-01/report.json`: `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`
- `research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl`: `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`

## One-shot commands

```sh
python3 research/doom/analyze_map01_held_input_occupancy_fulltrace_v6.py research/doom/results/map01-v38-integrated-threat-live-01 --out research/doom/results/map01-held-input-occupancy-fulltrace-v6/v38.json
python3 research/doom/analyze_map01_held_input_occupancy_fulltrace_v6.py research/doom/results/map01-v39-coast-liveness-live-01 --out research/doom/results/map01-held-input-occupancy-fulltrace-v6/v39.json
python3 research/doom/audit_map01_held_input_occupancy_fulltrace_v6.py --repo . --candidate-dir research/doom/results/map01-held-input-occupancy-fulltrace-v6 --out research/doom/results/map01-held-input-occupancy-fulltrace-v6/audit-v6.json
```
