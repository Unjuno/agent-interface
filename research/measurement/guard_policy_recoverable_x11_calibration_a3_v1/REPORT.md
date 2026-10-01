# Recoverable X11 guard calibration A3 — retained result

Issue #1793. Lineage: #1646 → #1672 → #1722 STOP → #1777 construction FAIL → #1793.

## Disposition

**PASS_GUARD_POLICY_RECOVERABLE_X11_CALIBRATION_A3_SCOPED**

Formal1 / reruns0 / replacements0 / tuning0.

This is the first rung in this lineage that both identifies the same-route cost parameters and completes the held-out guard-policy comparison.

## One changed factor from #1777

Route, fixture, ROI, 120 ms known-success observation envelope, 3 ms stale-no-effect envelope, baseline subtraction formulas, q tiers, formal corpus, bootstrap count and #1646 selector are unchanged.

Only the cost-identification rule changes:

- #1777 incorrectly required every noisy paired baseline-subtracted timing difference to be nonnegative;
- A3 estimates the **expected paired increment** with the raw paired sample mean;
- identifiability requires the preregistered 95% paired-bootstrap lower endpoint for each selector cost to be >=0;
- negative individual samples are legal evidence and would be retained without clipping, winsorization or deletion.

In this formal block all three negative-sample counts happened to be zero; that is an observed result, not an additional gate.

## Formal calibration

Same route population, wall-clock milliseconds only:

| Parameter | Estimate | 95% paired bootstrap |
|---|---:|---:|
| guard cost c_g | 0.084453 ms | not used as an uncertainty gate |
| sensitivity s | 1.0 | exact on 128 stale probes |
| false reject f | 0.0 | exact on 128 fresh probes |
| c_y_stale | 5.891999 ms | [5.696354, 6.113504] |
| c_y_fresh | 5.813674 ms | [5.635865, 6.005154] |
| c_f | 9.741530 ms | [9.262726, 10.439986] |

All formal cost-identification lower bounds are positive.

Recoverability checks also pass:
- every stale old-point first attempt is independently logged as a no-op before fallback success;
- every episode reaches the same success terminal;
- terminal pointer/button state is neutral;
- primary and independent audits pass.

## #1646 break-even on this route

With s=1 and f=0:

`p* = c_g / (c_f - c_y_stale)`.

Using the formal calibration:

- `c_f - c_y_stale = 3.849531 ms`;
- `p* = 0.0219386`;
- fixture-population break-even ≈ **2.194% stale-at-admission probability**.

This is not a deployment stale probability or production threshold. The q tiers below are preregistered experimental populations.

## Held-out policy transfer

Each tier contains 256 matched PRE_GUARD/POST_ONLY pairs with an identical stale schedule across arms.

| q tier | realized p | # stale | predicted | observed paired 95% CI, PRE−POST | observed |
|---|---:|---:|---|---:|---|
| 1/100 | 1.5625% | 4 | POST | [-0.031, +0.146] ms | UNKNOWN |
| 1/20 | 5.0781% | 13 | GUARD | [-0.240, +0.028] ms | UNKNOWN |
| 1/5 | 25.7813% | 66 | GUARD | [-0.933, -0.403] ms | GUARD |
| 1/2 | 48.8281% | 125 | GUARD | [-2.495, -1.465] ms | GUARD |

Two tiers are statistically resolved, both in the direction predicted by the independently calibrated #1646 selector. Selector disagreements among resolved tiers: **0**.

The lower-q tiers remain UNKNOWN because their confidence intervals cross zero. They are not forced into a policy verdict merely because the point-estimate selector has a sign.

## Why this does not contradict #1777

#1777 failed its **construction gate** because one noisy matched difference per cost family was negative despite positive means. A3 changes the object being identified from samplewise monotonicity to expected incremental cost. That is the only scientific change.

A3 construction and formal both require the uncertainty interval for the expected cost to exclude negative values. No #1777 row is pooled.

## Source and audit integrity

Before formal, the initial Git publication accidentally contained stale predecessor bytes in five of seven source chunks. Formal remained0. Local science source did not change. Those five remote chunks were replaced and the final mandatory readback matched the frozen local Git blobs7/7. This incident is retained in `PREFORMAL_PUBLICATION_REPAIR.json`.

Postformal science-file SHA-256 matches the freeze6/6.

Primary audit:
- PASS
- six corruption controls PASS.

Independent audit:
- imports no experiment module;
- calibration groups checked128;
- policy rows checked2048;
- stale-noop episodes checked336;
- errors[].

## Raw-evidence boundary

The exact formal result is 2,246,591 bytes, SHA-256:
`e14dfa8a80c904e41a98f2eae153f82d3e374322b0862d863c0468b9e16cd2d5`.

Deterministic gzip is153,442 bytes, SHA-256:
`0d01b537526a49e2785b75c7aa0a8e939dcefa670789f23b335382df2217135b`.

The full raw JSON is not duplicated into GitHub. The branch retains the exact reconstructible science source, compact formal summary, both audits and cryptographic raw commitments. No rerun or summary substitution occurred.

## Scope and non-claims

This is one synthetic private-X11/Tk route intentionally designed so stale action is a benign no-op and is fully recoverable. It validates **same-population calibration mechanics** for #1646, not:

- deployment stale probability;
- production compositor/runtime timing;
- irreversible or hard-safety routes;
- model/token benefit;
- human-tempo operation;
- general GUI reliability.

Hard-safety routes remain mandatory-pre-guard under #1646's safety override.

## Next legal rung

Do not add another guard mechanism.

The next high-information step is to transfer the frozen calibration method to one naturally occurring **recoverable** route where stale incidence is passively observed rather than authored. That route must keep all costs in one declared dimension and must not turn wrong-target/irreversible effects into finite recovery costs.
