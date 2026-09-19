# Censored-down temporal gate v1 — construction evidence

Issue: #984  
Task: `USEFUL-EFFECT-CENSORED-DOWN-TEMPORAL-GATE-20260917-001`  
BASE: `b488c44c49059b6cf1385ecd43b32a16ce7a9fd5`  
Status: **CONSTRUCTION_PASS / FORMAL_NOT_AUTHORIZED**

Direct parents are the formal #981 dual-edge occupancy result and the formal #974 provenance-composition result. This rung changes only the bound-effect temporal gate required when the physical press edge is interval-censored.

## H

For a scored effect with valid lineage bound to an actuation whose physical press is `down ∈ [down_lo,down_hi]`:

- `t < down_lo` is definitely before the press and is `invalid_temporal`;
- `down_lo <= t < down_hi` has unresolved order and is `temporal_ambiguous`;
- `t >= down_hi` is guaranteed not to precede the press under #974's equality convention and continues to `useful_bound` / `nonuseful_bound`.

All earlier #974 gates retain precedence. Exact `down_lo==down_hi` must reduce exactly to #974 and never produce ambiguity.

## T

Disposable standard-library container only. No X11, model, provider, GUI, task input or network action.

Construction used seed `98420260917001`, 12 fixed precedence/boundary controls, a 9,856-row exhaustive small-domain temporal sweep, 200,000 random mixed cases containing 600,789 effect records, and an independent endpoint-enumeration oracle. Occupancy neutrality was checked against a separately implemented integer point-set reconstruction of #981-style physical/authorized bounds.

## D / result

Construction passes:

- fixed controls: 12/12;
- exhaustive candidate/oracle: 9,856/9,856;
- exhaustive ambiguous rows: 240;
- random cases: 200,000/200,000 exact bucket-count agreement;
- random effect records: 600,789;
- ambiguous -> bound promotions after corrected per-record diagnostic: 0;
- exact-down degeneration: exact #974 rule, ambiguity 0;
- effect presence/absence changed no independently recomputed occupancy bound;
- construction digest: `ec7e3f511f37cd3019c9159717ea3507054819d11c267dfaa380f67c6d92e395`.

Corrected-audit wall was 22.49 s and max RSS 93,228 KB on the construction container. These are diagnostics, not performance claims.

## Retained diagnostic correction

The first construction test printed `ambiguous_to_bound_promotions=0` using a logically vacuous diagnostic expression. That counter did **not** drive the scientific result: exhaustive/random per-row candidate-oracle equality already covered the temporal gate. The first result was preserved, only that diagnostic computation was changed to compare the independent oracle role against a per-record candidate role, and the same frozen seed/corpus was re-audited. The corrected audit again reports zero ambiguous-to-bound promotions and produces byte-identical result JSON / result SHA-256.

First and corrected result SHA-256: `38b2ffca0d1d0ef94beedd72e6b4d2e2cff78234f48cfd60061ff1451e772822`.

## C

Temporal non-precedence is not task causation. A real application callback may use another process/clock or resolution. Even `t>=down_hi` only means the event timestamp does not precede any admissible press under this model.

## U / stop

Synthetic same-process integer-time construction only. No real X11 press time, application consumption, MAP01 usefulness, human tempo, token/latency or production ABI claim. `formal_authorized=false`; a separately frozen fresh formal successor is required for a scoped PASS.
