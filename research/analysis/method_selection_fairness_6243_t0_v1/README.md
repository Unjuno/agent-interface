# Issue #6243 T0 — method-selection fairness

## H / T / D / C / U

**H.** In a matched desktop task, natural-method human/agent tempo and a descriptive common-method comparison can differ because the arms use different method mixes. The null is plausible.

**T0.** First audit the retained #57, #5592, #6136 and public six-task evidence for a matched human cohort, permitted methods, choices, failed attempts, timing and acquisition costs. Separately validate the finite accounting rule on blinded constructed attempt rows with planted route/method asymmetry, a method switch, a failed attempt, and a null. Preserve every duration and outcome; compare natural mixture, common-method descriptive timing, and acquisition-inclusive horizons.

**D.** A synthetic `METHOD_PASS_SCOPED` requires both independent annotators to agree at or above the frozen 0.90 threshold, all attempts/costs to remain in the denominator, the planted asymmetry to appear in natural mixture but not the equal-method null, and mutation controls (dropped failure, hidden switch, arm-visible coder) to fail. This cannot qualify real people, agents, or GUI effects.

**C.** Model/host waiting may dominate method differences; methods and shortcut eligibility may be legitimate interface advantages.

**U.** Constructed rows cannot establish human tempo, a population effect, external validity, or causal within-method effects. Method choice is endogenous; common-method summaries are descriptive only.

## Intake / stop boundary

Current main at freeze: `fe37b6913f75706fc6bd536ae3afd6ed6a72b674`.

The retained public six-task comparison is one agent-vs-agent serial pair and explicitly has no human comparator. #5592 and #6136 are unverified proposals and say the matched human data/cohort are absent. Thus the real-data eligibility rung is **`HOLD_NO_MATCHED_METHOD_DATA`**. Do not synthesize human rows into the historical dataset or rescore its HOLD.

## Construction history and method-only result

One pre-freeze construction/audit attempt failed because the candidate serialized operator tuples as JSON arrays while the independent auditor compared them to in-memory tuples. Root cause: JSON round-trip type normalization, not a scientific discrepancy. The failing output was construction-only and superseded before freezing; no formal allocation was spent. After correction, the 11-assertion construction suite passes and its three planned mutations are rejected. See `RESULT.md` for the frozen one-shot method validation.

## Execution boundary

The constructed accounting check is host-only because an unrelated container `unjuno-native-ci-6092` was running and coordination Issue #5085 prohibits launching another Docker container without explicit slot release. We did not inspect, stop, or modify it. `obstac` is absent from the available CLI/tool inventory. This is a method-construction check, not the missing empirical comparison.

See `cases.json`, `key.json`, `annotator_a.py`, `annotator_b.py`, `candidate.py`, `auditor.py`, `candidate.json`, and `audit.json` for exact data and gates. The two coders are independent deterministic annotation implementations, not human raters; 100% agreement is fixture/codebook agreement only.
