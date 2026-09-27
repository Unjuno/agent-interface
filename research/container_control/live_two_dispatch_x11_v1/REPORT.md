# Live X11 `authority_ended` two-dispatch integration v1

Status: **PASS_LIVE_TWO_DISPATCH_X11** for a frozen model-free three-pair block. This is live input/freshness semantics evidence, not model/DOOM efficacy or production promotion.

## Question

Can the previously retained two-dispatch session rule survive real X11 actuation?

The rule is:

1. a first physical input authority ends independently at an owner deadline;
2. input release is verified empty;
3. one passive post-release pixel observation becomes evidence only, not renewed authority;
4. a second semantic dispatch requires a strictly newer current observation and the unchanged adaptive caller v3 ordinary revalidation path;
5. the second physical action uses a **new, separate Lease**;
6. reusing the post-release observation as the current observation must stop before any second input.

## Live fixture

A private Xvfb/XTest rendered tracker derived from the existing container-control fixture is used with exogenous drift disabled. Controller logic sees only the rendered marker pixels. Exact application x and app-observed key events are posthoc scorer/audit channels and are never passed into caller decisions.

First action: Left under an independent 120 ms owner deadline.

After owner-verified expiry, the controller captures the post-authority marker frame and opens a sequence-bound one-use replan token. Two conditions are matched:

- **FRESH**: take one strictly later current pixel observation; run exact caller v3 `reuse_revalidate -> final_revalidate`; execute a separate Right action under a new Lease; verify the visible pixel effect.
- **STALE**: reuse the post-authority observation as current. Caller must return `SAFE_STOP / stale`; no Right key may be physically pressed.

## Frozen design

Three matched pairs, alternating order:

1. FRESH → STALE
2. STALE → FRESH
3. FRESH → STALE

Hard gates:

- first owner release is `expired` and verified in all six arms;
- final owner key state is empty in all six arms;
- pixel decoder error `< 0.03`;
- FRESH 3/3 reaches `TASK_SUCCEEDED` only after ordinary call order `reuse_revalidate, final_revalidate, execute, verify_effect`;
- FRESH has exactly one Right KeyDown and independent exact effect delta `> 0.015` in all three arms;
- STALE 3/3 returns `SAFE_STOP / stale`, zero Right KeyDown and no execute.

## First formal outcome

Decision: **PASS_LIVE_TWO_DISPATCH_X11**.

- FRESH pass: **3/3**;
- STALE pass: **3/3**;
- Right KeyDown: FRESH **3**, STALE **0**;
- all first authority releases: `expired`, verified;
- all final owner key states: empty;
- max pixel-decoder error: **0.008229653**;
- minimum independent exact FRESH effect delta: **+0.047061297**.

Fresh exact effect deltas across the three arms were approximately `+0.0471`, `+0.0586`, `+0.0586` normalized x units. Stale controls never generated the second physical input.

Formal first-result SHA-256: `01a707dfd24e597929ebb91c1310e427e0b5cfeeefeed20812d46d7df9598017`.

## Interpretation

This moves the boundary from transcript semantics to physical input:

- owner deadline termination of the first capability is real;
- post-release pixel evidence does not itself authorize a new action;
- a strictly newer current observation plus ordinary caller revalidation is required;
- the new action obtains its own independent Lease;
- stale-current evidence produces zero second physical input.

The architecture therefore behaves like a capability system: expiry destroys the old actuation capability, evidence can justify reconsideration, and a new side effect requires a fresh capability/admission path.

## H / T / D / C / U

**H.** Sequence-bound post-authority replan evidence can safely bridge two live input dispatches without authority carryover.

**T.** Three alternating matched X11 pairs, six real XTest sessions, exact caller v3, real InputOwner expiry/release, pixel-only controller observations, posthoc exact state/input audit, zero model calls.

**D.** PASS because all fresh arms execute and independently move the marker, all stale arms stop with zero second KeyDown, and every release/freshness/decoder hard gate passes.

**C.** This is a deterministic single-object movement fixture. The next-domain application may have ambiguous effects or delayed semantic feedback; a fresh pixel sequence can still be semantically insufficient.

**U.** No frontier model, no ViZDoom, no concurrent external mutation, no network-delivery race, one X11 host family. Next high-information gate is to use the same live boundary on one existing real-MAP01/desktop recovery session with a delayed or changed post-release observation, but only after checking current parallel leases to avoid consuming a duplicate formal allocation.
