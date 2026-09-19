# MAP01 bounded recovery-cover matched preregistration v1

Status: **CONSTRUCTION FROZEN; NO LIVE LEASE GRANTED**

Task: `O4-PH48-RECOVERY-COVER-MATCHED-001`  
Base: `a0abe6cf31bd68a416c02fa417baab3704533bfc`

## Why this lane exists

`main` already contains the non-overlapping measurement work needed to make the next live comparison interpretable: interval-censored held-input reconstruction, release-edge telemetry construction, and an independent scorer clock whose terminal state is locked per scorer epoch. Other agents are already working those measurement lanes. This task therefore does not edit them and does not start a competing live allocation.

The remaining high-information question is narrower: when the slow planner is pending, does an explicitly authorized bounded recovery program reduce input-free wait relative to unauthored coast without weakening stale-authority refusal, release correctness, or independent outcome quality?

## Frozen comparison

Two matched arms are defined in `map01_recovery_cover_matched_v1_prereg.json`:

1. `COAST_CONTROL`: unauthored empty coast; no input authority.
2. `BOUNDED_RECOVERY`: a separately admitted bounded recovery program with source binding, observable guard, expiry, cancellation on guard failure and verified empty release.

Everything else is required to match: initial fixture and seed schedule, model, prompt/schema, resolution, game speed, observation path, input backend, independent scorer contract and release telemetry contract. The only intended arm difference is planner-wait fallback behavior.

This construction intentionally does **not** define a new privileged game-state channel and does not deliver independent scorer events to the controller.

## Safety boundary

Recovery authority must be explicit and independently admitted. It may not silently rebase an old health/damage budget, survive observable guard failure, exceed the frozen 1500 ms single-lease cap, omit source-observation binding or expiry, or claim success without verified empty release.

Any stale-authority admission, release failure, privileged scorer leakage, or accepted program lacking terminal release is an immediate FAIL.

## Measurement boundary

The frozen primary outputs are planner wait, held-input lower/upper bounds, no-held-input lower/upper bounds, first positive/negative independent scorer event, verified release latency, stale-authority admissions and release failures.

The preregistration deliberately permits `UNCERTAIN` when clock alignment or interval width prevents a directional claim. This is preferable to converting a measurement gap into a positive result.

## Product Hunt consequence

If a separately leased live allocation passes, the defensible demonstration is not “AI plays DOOM at human speed.” It is the narrower and more legible claim:

> During some slow-planner waits in this matched MAP01 test, an explicitly bounded local controller continued authorized input, while stale evidence still caused cancellation and verified release.

A synchronized timeline should show planner wait, admitted/held input, guard transition, release edge and independent scorer event on one mapped monotonic clock. A lucky MAP01 clear is useful only if independently observed; it is not a substitute for the matched mechanism evidence.

## Container verification

Local network access was unavailable, so repository state was read through the GitHub connector and these new files were tested in an isolated container.

Commands:

```text
python3 validate_map01_recovery_cover_matched_v1.py map01_recovery_cover_matched_v1_prereg.json
python3 -m py_compile validate_map01_recovery_cover_matched_v1.py
```

Result: **PASS** for schema validation and synthetic fail-closed gate checks.

Frozen SHA-256:

- prereg JSON: `5463fc258685b34fa0b2ff3dde00859a3f4349568428cc258e5f543f337ea40c`
- validator: `eaf735fd30e03401375de8767b4f7b5254a652b1aa38a0c3eceb57d2e27c3294`

These checks establish only construction integrity. They provide no live efficacy claim and no live-experiment authority.

## H / T / D / C / U

**H — falsifiable hypothesis.** Under matched MAP01 conditions, explicit bounded recovery can reduce the no-held-input planner-wait upper bound relative to unauthored coast while preserving zero stale-authority admissions, zero release failures and no earlier harmful independent outcome.

**T — minimum test.** A separately leased first-outcome matched allocation uses both frozen arms under the same fixture/seed schedule and instrumentation. At least one recovery interval must actually hold acknowledged input before planner completion; otherwise the mechanism was not exposed.

**D — disposition.** PASS/FAIL/UNCERTAIN/HOLD are frozen in the JSON. Safety gates are hard. A non-exposed recovery path is UNCERTAIN, not PASS.

**C — competing explanation.** Recovery may simply add movement without useful task effect, may accelerate harm, may rely on stale semantics, or may appear to reduce idle time only because release/clock telemetry is misaligned. The matched scorer/release requirements are intended to distinguish those cases.

**U — uncertainty.** The dominant remaining uncertainties are the exact recovery policy to be exposed, live clock alignment, sparse independent progress events, and whether one fixed MAP01 fixture transfers to desktop/planning tasks. No broad promotion should follow from a single passing pair.

## Coordination rule

This branch owns only the preregistration/validator paths above. A different agent may implement or execute the live runner, but should use an immutable base and a new formal lease/result path. It must not rewrite these frozen files after seeing a live outcome.
