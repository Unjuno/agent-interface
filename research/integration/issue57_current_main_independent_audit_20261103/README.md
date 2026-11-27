# Issue 57 current-main audit and observation-image binding

Date: 2026-11-03
Repository: `Unjuno/agent-interface`
Base and remote `main` at verification: `e0ea80b956e77c1e3f8e03866c6e1d5811ce6d71` (verified with `git ls-remote origin refs/heads/main`). Python: Windows CPython 3.11.9.

## Work performed

This packet independently re-runs three published WSLc Calc comparison auditors from the exact current-main tree and the local synthetic composition regressions. It also records a small composed-path test repair: the App Server success and stale-generation fixtures previously passed the literal bytes `synthetic observed image` even though public MCP returned an image. Both tests now decode the one returned PNG, validate it, pass those bytes to the App Server planner, and assert byte identity at planner entry.

No runtime code changed. No model/provider was called. No WSLc or Docker container/allocation was started for this packet. The comparison reports below are re-audits of already-published runs, not new experimental trials.

## Re-audited published results

| Published block | Attempts / route medians | Input token medians | Output token medians | Independent task/release audit |
|---|---|---|---|---|
| Fixed-task three-arm, forward plus reverse | 6 attempts; task seconds direct 6.258, compiled 6.561, fresh 9.659 | 12,185 / 12,185 / 25,743 | 62 / 78 / 132 | All six saved exact 472/615 and neutral X input |
| Temporary-overlay three-arm, forward plus reverse | 6 attempts; task seconds direct 9.278, compiled 10.150, fresh 12.096 | 25,751 / 25,751 / 40,666 | 148 / 140 / 194 | All six saved exact 472/615 and neutral X input |
| Temporary-obstruction matched recovery, forward plus reverse | 4 attempts; task seconds compiled 9.622, fresh 13.891 | 25,771 / 40,722 | 132 / 210 | All four independently scored saved 731/864 and neutral X input |

The audit outputs retain per-attempt records, including cache counts and launcher intervals. Cached input is included in input tokens. The source READMEs document two samples per arm, fixed fixtures and scripted Save. The overlay is removed by the test before fresh grounding; it is not a runtime stale-handle refusal or persistent-obstruction recovery. These results do not establish population speed/cost/reliability, general recovery, partial-input recovery, MAP01, or project completion. The three-arm results also show the direct route was faster than compiled in both paired blocks, so the evidence does not justify saying compiled execution is the fastest route.

## Local checks

- `runtime.core_v1.test_compiled_gui`: 33/33 normal and 33/33 under `-O`.
- App Server to public-MCP adapter tests: 3/3 normal and 3/3 under `-O`.
- Provider-to-public-MCP composed endpoint tests: 10/10 normal and 10/10 under `-O`, including the image-identity assertion added in this branch.
- Three published archive comparison auditors: status `audited` for each.

Full stdout/stderr and exit codes are retained alongside the JSON comparison results. `inspect_synthetic_observation.py` is a bounded Fake X/public-MCP observation-only diagnostic used to inspect the synthetic screenshot; it issues no input. One initial audit harness setup error from the sparse checkout and one pre-fix script-import recursion are described in `setup-errors.txt`; neither is a scientific trial and neither modified the published source data.

## What the test repair establishes

It prevents the synthetic success and stale-generation tests from silently giving the fake planner an unrelated placeholder image. Each planner receives the exact PNG bytes returned by the public observation in the same composed attempt; the stale-generation case then changes process generation while the planner turn is pending and verifies refusal before dispatch.

It remains a Fake App Server/Fake X contract test. The planner's tool request is still fixture-authored; byte identity does not establish that a real model understood the image, that upstream provider retries are completely accounted, or that the production caller always binds the correct image. A live model/provider attempt with provider-side usage reconciliation remains required for those claims.

## Current disposition

Issue #57 is open and explicitly retains broader cold/warm/invalidation/repair, complete lifecycle accounting, partial-input and persistent-obstruction recovery, and live provider gates. Issue #7924 remains STOP/HOLD for shared WSLc client/container ownership. A zero visible `wslc.exe` process snapshot does not resolve persistent session ownership, so this packet did not issue WSLc RPCs or create an allocation. No WSLc/MAP01 completion claim follows.

## Files

- `three_arm_reverse_pair.json`, `obstruction_reverse_pair.json`, `matched_recovery_reverse_pair.json`: independent re-audit outputs.
- `*_normal.log`, `*_opt.log`, and corresponding `.exit_code.txt`: local test evidence.
- `inspect_synthetic_observation.py` and its `.log`: synthetic screenshot inspection procedure and output.
- `setup-errors.txt`: preserved local harness setup errors and their scope.
- `SHA256SUMS.txt`: SHA-256 digests of this packet and the exact main source/raw archives checked.
