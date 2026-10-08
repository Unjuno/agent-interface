# Result — MAP01 v12 plan/step lineage R0 (#1907)

Decision: **`PASS_MAP01_V12_PLAN_STEP_LINEAGE_R0_SCOPED`**.

## What this closes

The current MAP01 v13/v3 release path can serve as **program/step attribution metadata** for an independently authoritative v12 physical actuation without laundering v3 into physical truth. The bridge is accepted only when:

- the MAP01 release is an ordinary, post-batch verified v3 transition;
- the v3 row remains explicitly `physical_verification_authoritative=false`;
- v12 DOWN/UP are both `CONFIRMED_PHYSICAL_DOWN/UP`;
- v12 `{actuation_id, owner_id, intent_token, key}` matches across both edges;
- MAP01 `{owner_id, intent_token, key}` matches that v12 lineage;
- batch identifier/step/size/positions form one complete one-to-one batch;
- the v12 UP interval is nested inside the same outer MAP01 release-RPC interval;
- physical and outer release intervals are copied unchanged; no exact endpoint is synthesized;
- all produced records remain `grants_input_authority=false`.

This resolves the integration-readiness question caused by MAP01 `input_admission` being intentionally id-less: the release batch supplies `{identifier, step}`, while stable v12 `actuation_id` joins the authoritative UP edge back to its paired DOWN edge. The DOWN edge therefore need not be relabelled by timestamp proximity or by an inferred exact time.

## Frozen evidence identities

BASE `7f02687f8136ea6a390fc800900937adc227969c`.

- `session_map01_v13.py` Git blob `51c644ce424e41bb2cd3d401a52b6c9820f70135`
- `doom_retained_input_backend_v3.py` Git blob `65d3f1a7b21af09ab8fe10ef883e3e17a9f6cb27`
- `input_transition_owner_v3.py` Git blob `0ea631abcf6272f0538a9ef9198ad8069b47b464`
- retained v12 source SHA-256 `b63e8a925a5ff741385fb69b8cf20ac07e01a520f34607778d8d28a0256c1508`
- retained physical-edge adapter SHA-256 `ed7e4f00675e79a9ef86984c7c129bb6c3eda64855c6c71821c313c9feb9badf`

Parents are #443, #998, #1276, #1340 and #1425. No parent result is relabelled or rerun.

## First primary outcome

Exactly one primary invocation; reruns/replacements/tuning 0.

- directed controls: **21/21 PASS**
- exhaustive orthogonal cases: **4,096**
- exhaustive candidate/oracle mismatches: **0**
- fixed-seed randomized cases: **100,000**
- randomized candidate/oracle mismatches: **0**
- accepted randomized cases: **22,456**
- v3-only rows promoted to physical evidence: **0**
- accepted timestamp changes/narrowing: **0**
- authority expansions: **0**
- primary elapsed time: **4.248396363 s** in the disposable standard-library container
- case digest SHA-256: `62911a49e6b77b5b8fee19a742ca2a0239e4f6aa321b8402ea7587344e28ce26`
- `RESULT.json` SHA-256: `7b43277fa5e0036bd3ca100af013ffd47905f63a984c9a512109750d3adc3d4d`

The independent post-primary audit used a separate 20,000-case mutation corpus and returned mismatches0/errors[]. `AUDIT.json` SHA-256 is `09aa9cf624d2de579c7765804be2023a768bfac7f8aa74926b077bbc908f577a`.

## Negative controls retained

The bridge fails closed on current-v3-only input, nonordinary/unverified release, duplicate batch position, duplicate actuation ID, identifier/step mismatch, owner/intent/key mismatch, empty actuation ID, unconfirmed DOWN/UP, crossed edge intervals, authoritative-UP outside the outer release RPC, source drift, authority=true, v3 claiming physical authority, and incomplete key/pair sets.

## Scope / stop

This is **contract and integration-readiness evidence only**. It does not establish a new X11 edge, a MAP01 live physical hold, useful gameplay, a model-boundary speedup, recovery efficacy, matched human tempo, or production ABI compatibility. The container has Xvfb/Python-Xlib but no `vizdoom` module, and direct GitHub clone is unavailable because the container cannot resolve `github.com`; therefore this R0 intentionally does not fabricate a MAP01 live result.

The next justified successor is a fresh MAP01 live measurement that reconstructs the exact retained v12 producer, applies this bridge to the current v13 batch context, and measures physical held-input occupancy on a fixed no-model condition. Its live result must be separately leased/retained; this PASS is not that result.
