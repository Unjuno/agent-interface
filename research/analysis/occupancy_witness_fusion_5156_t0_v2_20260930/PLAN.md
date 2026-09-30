# Owner-release / server-witness interval fusion (T0 v2)

## Provenance and question

This is a construction-only successor rung for the r133/#59 held-input
occupancy measurement, related to #5156 and #4345. Predecessor attempt 01 is
preserved under `predecessor_attempt_01/` as `STOP_STALE_MAIN_BEFORE_RUN`: the
main SHA advanced after freeze and the candidate runner/import were invoked
zero times. T0 v2 is a new identity frozen against current main. It does not recover,
replace, or pool #4345's consumed 16 sessions; the published disposition there
remains `HOLD_PUBLICATION_INCOMPLETE`. It does not rerun #5156's construction
or consume its still-unspent X11 fixture allocation. The exact inputs below
are finite synthetic interval contracts, not records from a real key event.

## H — hypothesis

When an independent X-server state witness and an input-owner release bracket
refer to the same key, actuation, owner, display incarnation, and monotonic
clock, the feasible logical key-up interval can be narrowed by intersecting
their conservative intervals without excluding any compatible hidden event
time. Incompatible, missing, malformed, or empty evidence must return
`UNKNOWN`, never an exact timestamp or authority.

## T — frozen construction experiment

Allocation identity: `R133_OCCUPANCY_WITNESS_FUSION_5156_T0_V2_20260930_01`.
Compare a candidate interval fusion function against a separately implemented
finite hidden-time oracle. Enumerate every pair of DOWN/UP observation query
intervals over integer time 0..4 and every ordered owner
`KeyRelease-request-start <= request-return <= XSync-return` triple over the
same domain. For each valid source identity, enumerate all latent DOWN snapshot,
release, and UP snapshot times consistent with both reports. Add corruption
controls for owner, actuation, key, display incarnation, clock, missing witness,
duplicate release, re-press, inverted brackets, malformed integer fields, and
empty intersections. The output is a proposal-only interval or `UNKNOWN`.

The one-shot output is `results/t0-02/raw.json`. This rung runs on CPython on
the Windows host because coordination Issue #5085
has no exact CPU/Docker allocation for this task. No Docker/OrbStack CLI, X11,
GUI/input, game, model/provider, GPU, network, or user data is used. The formal
#5156 X11 measurement remains unspent and gated.

## D — decision rule

`PASS_INTERVAL_FUSION_CONSTRUCTION_ONLY` requires candidate-bounded integer
release times to equal the independently enumerated hidden-time set for every
valid exhaustive case; every compatible release must be retained; no
incompatible/corrupted case may produce a bound; authority must remain false;
and the result/audit/source hashes must reconcile. Any omitted compatible
time is `FAIL_UNSOUND_NARROWING`; any malformed or identity-invalid evidence
that produces a bound is `FAIL_OPEN_EVIDENCE`; missing execution/audit evidence
is STOP/HOLD, not a scientific FAIL.

## C — assumptions and competing explanations

The calculation assumes exact shared monotonic-clock units, one X-server
incarnation, one key/actuation, a single DOWN-to-UP transition, no re-press,
and that XSync return bounds processing of the preceding release request.
Timestamp intervals are conservative brackets; their endpoints are not exact
physical HID or application-consumption times. A strict interval intersection
may provide no usable bound even where one evidence source alone was valid.

## U — limits and next evidence

This tests only interval-contract composition over synthetic discrete time. It
does not demonstrate XTest/XSync behavior, actual held-key duration, MAP01
control, useful task effect, recovery efficacy, safety rate, human tempo, or
cross-domain runtime transfer. The next empirical step remains the separately
assigned #5156 disposable X11 allocation on an exact current-main freeze. This
construction result cannot authorize or substitute for it.
