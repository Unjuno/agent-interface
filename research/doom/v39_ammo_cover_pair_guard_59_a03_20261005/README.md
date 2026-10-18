# Issue #59 — paired-epoch ammo-aware cover guard (A03 construction test)

## H / T / D / C / U

**H.** A02's two-guard prototype is unsafe to compose unless health and ammo come from the exact same observation epoch. A small pair gate using exact integer sequence/time types and equal binding should fail closed on split or malformed samples before either signal guard can preserve an existing fire cover.

**T.** Freeze current-main `ObservableSignalGuard` plus a fixed source pair and ten current-frame cases. The candidate composes two instances of the frozen generic guard behind a strict paired-epoch validator. Cases cover coherent positive/boundary ammo, zero ammo, health below floor, sequence/time/binding disagreement, Boolean/float sequence aliases, and unavailable ammo. No Doom controller, game, model, GUI, OS input, or runtime source is changed or invoked.

**D.** PASS only if coherent positive ammo (including 1) preserves, zero ammo and health below floor invalidate, and every unavailable, split-epoch, binding-mismatched, Boolean, or float-typed pair invalidates. Independent audit must derive and match every row. Otherwise FAIL.

**C.** This pair gate may be duplicative of the real event producer's frame join, may over-abstain on recoverable HUD read skew, and may add latency or interrupt useful cover. No timing or controller integration is tested.

**U.** Construction semantics only. A PASS does not validate live typed-frame delivery, cover renewals, policy usefulness, cancellation, key-up, verified empty release, survival, or MAP01. Do not integrate or launch live behavior based only on this prototype; the separate Issue #59 live lane remains required.

## Runtime

The exact generic guard is stdlib-only. CPython 3.14.5 on macOS arm64; no container/isolation claim. A01 already retained OrbStack's read-only image-inventory error; no repeated daemon probe or image pull/build/restart is in scope.
