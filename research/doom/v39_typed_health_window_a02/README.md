# V39 typed-health short-window replay A02

## Why this follows A01

A01 was frozen but STOPped before candidate evaluation because its Node command failed to split JSONL. That exact STOP is preserved at `v39_typed_health_window_a01/runner-stop.json`; A01 is not relabeled or replaced. A02 froze a parser-safe successor before its sole candidate replay, against the same immutable v39 source blobs.

## H/T/D/C/U

- **H:** Two downward typed-health transitions within a short interval may surface deterioration before a model wait returns on the unauthored-coast path, while leaving a stable wait untriggered.
- **T:** Replay the six exact `controller_model_started_ns` to `controller_model_ended_ns` intervals against ordered typed health rows. A decrease is an adjacent pair of observed numeric health samples with a lower second value. A trigger is the second decrease when two decreases are no more than W apart. Frozen W sweep: 0.5, 1, 1.5, 2, 2.5, 3, and 4 seconds. Report all waits; no selected threshold is treated as validated.
- **D:** Base `2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0`; report blob `bff2459036dcdcc44ed100b0c0bc657e1bb8e69a`; events blob `cbaeed9c7ba27b53cef9d10730ae33313371ad9a`; guard blob `c0955f976e3a0af6ce926f22cee4a5ddf70ef543`. 634 JSONL records, 218 typed observations, six report waits.
- **C:** One candidate replay; reject inconsistent source counts. Unknown/missing health clears the prior-sample chain. Primary subset is waits with `cover_policy_source_iteration == null`. No runtime, model, game, input, interrupt acknowledgement, or task outcome is simulated.
- **U:** Saved-only feasibility/sensitivity result for one trajectory. It cannot estimate a false-interrupt rate (only one stable no-policy wait), prove causality, or authorize a live controller policy.

## Result

At W=2.0s, the rule triggers in one of two worsening no-policy waits: decision 2 at sequence 81, 3.194s after model start with 3.113s until natural model end. At W=2.5s, it triggers in both worsening no-policy waits: decision 2 at sequence 81 (3.194s after start; 3.113s remaining) and decision 3 at sequence 103 (3.405s after start; 3.320s remaining). The one stable no-policy wait, decision 0, has zero decreases and never triggers at any horizon.

Important counterevidence: W=2.5s also triggers in authored-policy decisions 4 and 5. Decision 4's trigger is only 0.726s before natural completion. Decision 5's trigger is sequence 200. The interval from sequence 200 to the existing hard-invalidation event at sequence 218 is **3.186s** (timestamps 55546847220240 and 55550033032859 ns). The separately reported **3.379s** is remaining time from sequence 200 until `controller_model_ended_ns`, not time to sequence 218. This correction does not alter the saved candidate result. The candidate therefore needs strict unauthored-coast scoping and must not replace existing authored hard bounds. Even that scope has only 2 worsening and 1 stable retained examples.

## Validation and raw outcomes

The candidate was executed once using Node.js 24.6.0 after A02 preregistration. It validated 634 JSONL rows, 218 typed observations and six waits. Raw source SHA-256s: report `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`; events `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.

The first independent auditor (v1) stopped after calculation because its isolated runtime lacked Web Crypto; its STOP is retained and does not count as a pass. A second independent Node.js audit enumerated every qualifying transition pair and matched all 42 candidate/wait/horizon slots and both source SHA-256s. See `result.json`, `audit-v2.json`, and the candidate/auditor source files.

## Interpretation

This narrows a possible future trigger but does not demonstrate useful interruption, reduced model latency, token savings, freshness, correct next plan, or safe input. Any prospective live comparison must be newly authorized and preregistered, preserve original hard validity/release, and measure false interrupts, time to next eligible plan, interrupted-call usage, current-action admission, and task effect.
