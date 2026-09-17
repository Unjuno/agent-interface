# H/T/D/C/U — dual-edge interval occupancy v1

H: Given a key-down transition censored to [down_lo, down_hi] and release transition censored to [release_lo, release_hi], physical occupancy during a model-wait interval can be conservatively bounded without choosing a synthetic exact down timestamp. Lower uses [down_hi, release_lo] when positive; upper uses [down_lo, release_hi]. Authority bounds intersect those envelopes with explicit authority intervals.

T: Pure stdlib/container. First reproduce why exact-down projection is unsafe. Then fixed edge cases, 100,000 seeded random interval traces, and 50,000 fresh small-domain traces checked by independent exhaustive enumeration of all feasible exact down/release realizations. No X11/model/GUI/network/input. No existing formal allocation consumed.

D: PASS construction iff every realization occupancy lies inside candidate lower/upper bounds; per-actuation candidate lower equals exhaustive minimum and upper equals exhaustive maximum; authority bounds remain <= physical bounds; impossible temporal evidence rejects; exact-edge case reduces to parent semantics.

C: Aggregate lower union can be conservative rather than globally tight when several uncertain actuations interact. A future backend may provide exact transition timestamps. Clock-domain mismatch can invalidate interval comparison and is not solved here.

U: Synthetic integer time only; no claim that current X11 timestamps share a sufficient clock/provenance contract. This is a measurement representation test.
