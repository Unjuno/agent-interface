# V39 typed-health short-window coalescing A01 — preregistration

Status: FROZEN BEFORE CANDIDATE RUN
Issue: #59 (real-time control during frontier-model latency)
Base main: `2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0`

## H/T/D/C/U

- **H:** On the retained six-wait v39 typed-health stream, requiring two separate downward health transitions within a short window can surface a worsening unauthored-coast interval before natural model completion, while leaving a stable wait untriggered. This is a replay-feasibility hypothesis, not an efficacy claim.
- **T:** Replay the exact ordered `typed_observation` records against each report's `controller_model_started_ns` / `controller_model_ended_ns`. For each wait, compare the latest valid health sample at/before model start with in-wait samples. A downward transition is one adjacent pair of observed health samples with a strictly lower current value. A trigger occurs at the second downward transition if two such transitions are separated by no more than a frozen horizon W. Sweep all W in {0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0} seconds; do not select a winner after seeing the output. Report all six waits, separately identifying no-policy waits by `cover_policy_source_iteration == null`.
- **D:** Pin report blob `bff2459036dcdcc44ed100b0c0bc657e1bb8e69a`, event stream blob `cbaeed9c7ba27b53cef9d10730ae33313371ad9a`, and guard implementation blob `c0955f976e3a0af6ce926f22cee4a5ddf70ef543`, all read from base main above. The report audit confirms 218/218 typed observations reconcile.
- **C:** One deterministic, no-retry, saved-data replay. A valid health row must have `status == observed` and a numeric value. Missing/unknown rows clear the previous-value chain. Only transitions whose second sample lies within the model-wait interval count. Trigger time is the second decrease's capture time. Do not simulate changing model output, interrupt acknowledgement, input, or task outcome.
- **U:** A01 only establishes candidate signal timing on one retained trajectory. It cannot estimate false-interrupt rate from one stable wait, establish event meaning or causal benefit, or authorize live interruption. Any prospective intervention requires a fresh, separately authorized allocation and independent scoring.

## Decision gates

- **PASS_SCOPED:** all six windows parse, source identities match, results deterministic across two independent implementations, and no source artifacts are rewritten.
- **FAIL:** frozen replay rule or source identity cannot be evaluated as specified; preserve the raw failure and do not silently alter the sweep.
- **HOLD:** source artifacts unavailable/inconsistent.
- **STOP:** any proposal to launch game/model/input, reuse a consumed allocation, or treat replay output as permission for intervention.

No policy threshold, candidate trigger, or live allocation will be changed by this replay.
