# WSLc Chromium: capture-to-submission latency recount

This independently recounts two retained six-task, three-arm runs, `wslc_model_three_arm_preflight_20261031_a03` and `wslc_model_three_arm_preflight_reverse_20261031_a04`; no new model or GUI run was made. The executable audit pins both raw ZIPs by SHA-256, verifies each task against the fixture's saved submission history and final independent exact-count report, matches layouts across arms, checks recorded releases and reconstructs `received_ns - source.capture_ns` for every task. Both timestamps are generated in the same Linux container monotonic clock domain. The endpoint is **server receipt of a submission**, not completion of independent scoring or confirmation to the user. It excludes preflight, startup, initial preparation before capture, cleanup and other gaps; it is not end-to-end task latency.

| Run | Plain median | Ephemeral median | Persistent median |
| --- | ---: | ---: | ---: |
| a03, ephemeral → plain → persistent | 2.748 s | 4.947 s | 2.254 s |
| a04, persistent → plain → ephemeral | 3.883 s | 4.315 s | 2.224 s |

Each median summarizes six different task phases, not six independent replications. For the four persistent reuse tasks (2, 3, 5, 6), the paired plain-minus-persistent capture-to-submission difference was positive in all eight observations: 0.742–2.782 s. The cold task and repair task were slower for persistent in both runs: differences were −2.542/−0.724 s and −1.599/−1.008 s respectively. This is descriptive of two fixed-order executions of the same six-task seed, not a population estimate or proof that the persistent path caused the difference. Model sessions, cache and phase differ; the methods do not have fully matched failure behavior.

All three arms submitted each expected token exactly once and their recorded releases were neutral in both runs; the independent oracle verifies this fixture, not arbitrary GUI correctness. The preflight-inclusive reports separately account for input/output tokens and durations; input-cache counts are subsets and provider cost is unknown. Their setup-plus-task sums also omit other startup and idle intervals. Neither these figures nor this recount demonstrate general latency improvement, reliability, MAP01 completion or a full end-to-end speedup.

**Metadata correction:** both retained `out/result.json` records still contain the copied scope string `no schema preflight`. The same packets contain three separately recorded preflight attempts, successful schema validations and usage records, and the published a03/a04 reports correctly describe preflight inclusion. Preserve the original scope field unchanged as a historical inconsistency; do not treat it as evidence that preflight was absent or silently rewrite it.

Run `python audit.py` without optimization in a checkout containing both sibling raw archives. `audit-result.json` lists all per-task values and the original scope text. The auditor validates recorded timestamps and independent history; it does not rerun the browser, independently inspect the pixels, or infer missing intervals. Source workspaces and provider services were not newly verified by this recount.
