# Scene-scale-aware footprint revalidation through adaptive caller v3

## Disposition

**PASS_SCOPED_SCALE_INTEGRATION** for one-step Inkscape zoom in both directions. One frozen 32-case block completed once, without retry. Shared caller/runtime code was not patched.

## Mechanism

The fixed arm uses the original fixed-size target footprint. The scaled arm derives a local scale estimate from the already-required full-scene homography, resizes only the target footprint to that scale, then takes a **new target screenshot** before matching. Homography/scale evidence grants no authority. Scale outside the frozen [0.65, 1.55] interval fails closed. Both arms use the same shared caller, bounded search radius, ambiguity refusal, final fresh revalidation and ordinary InputOwner admission. Model fallback is disabled.

## Formal result

Two fresh scene seeds, zoom -1/+1, stable/moved/substitute/duplicate conditions, fixed/scaled arms, alternating order: **32/32 cases completed**.

- scaled stable: **4/4 correct edits**, no local repair required;
- scaled moved target + old-location same-color decoy: **4/4 correct edits via local repair**;
- scaled substitute/duplicate: **8/8 SAFE_STOP, task input 0**;
- fixed-scale stable/moved under zoom: **8/8 SAFE_STOP, task input 0** rather than risky recovery;
- fixed-scale substitute/duplicate: safe negatives preserved;
- wrong-target deletion: **0/32**;
- model calls/model wait: **0/0**;
- InputOwner release records: **528**, all verified empty;
- paired pre-controller screenshots: **16/16 exact-byte-identical**.

Observed scene-scale evidence spans 0.7067 to 1.4153; median scale was 0.7069 for zoom -1 and 1.4141 for zoom +1. Median target-footprint compute was 14.245 ms fixed vs 12.145 ms scaled. These are local compute measurements only, not end-to-end speed claims.

## Frozen-range boundary development probes

After the formal block, two out-of-range development probes were run without changing the frozen result. At zoom -2 the scene matcher returned `no_match`; at zoom +2 the homography implied scale about 2 and the explicit scale gate returned `unavailable`. Both stopped before task input with no wrong target. These probes support fail-closed range behavior but are not part of the formal denominator.

## H / T / D / C / U

**H.** Scene-homography scale can rebind a visual target footprint across one Inkscape zoom step in either direction, preserving unique target edits and refusing substitutes/duplicates through the shared adaptive caller with zero model calls.

**T.** 32 fresh Inkscape/Xvfb cases; 2 seeds x zoom{-1,+1} x 4 scenarios x fixed/scaled; alternating order; independent persisted-SVG scoring.

**D.** The frozen PASS rule was met for one zoom step each direction; arbitrary scale is not promoted.

**C.** Scene homography may fail under larger zoom; global scene scale need not equal local object scale; appearance is not semantic identity.

**U.** Two seeds; one zoom step each direction; Inkscape/Xvfb; fixture-authored reference.

## Architecture implication

A cached visual target need not be discarded solely because the whole scene changed scale. A fresh scene transform can update the **evidence geometry** without granting authority, after which the target still requires unique current appearance evidence and a later final revalidation. This separates geometric cache repair from semantic/input authority.

The executed shared caller is byte-identical to current-main Git blob `7faf042304728ce91a3e4f89d465b251ea0bf70d`; this study does not patch the caller. Full raw PNG/SVG/JSON evidence is retained outside GitHub and hash-bound by `EVIDENCE.json`.

Next gate: test nonuniform transform / DPI-like scaling and theme/color change separately. Do not widen the accepted scale interval from this result alone.
