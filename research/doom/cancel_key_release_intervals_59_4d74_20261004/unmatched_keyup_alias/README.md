# Unmatched key-up alias guard

This additive Issue #59 construction found that the prior explicit-key-up fix
used the current keysym mapping when no admission existed for the requested
logical key. A fake-Xlib counterexample admitted `W` at keycode 87, mapped
unadmitted `A` to 87, and requested `up(A)`. The prior owner released W's held
key even though no A admission existed.

The candidate now releases only a keycode recorded for the same lease and
logical key admission. An unmatched up is a no-op. The regression then sends
`up(W)` and confirms the original key is released.

Run `python3 -B -m research.doom.cancel_key_release_intervals_59_4d74_20261004.unmatched_keyup_alias.audit`
to check the baseline/candidate source pins, raw outputs, and ordered adjacent
suite. The baseline is the exact PR #7529 source at `9edcc73e5e`; no formal or
live allocation was consumed.

This is fake-Xlib source-composition evidence. It does not establish real X11
keymap delivery, per-key physical transition timing, semantic interpretation,
game/task effect, useful feedback, recovery, or live threat response.
