# Dynamic-focus X11 phase overlap A2

Issue #1762. Fresh output-capture-only successor to #1752. #1752 remains a protocol stop and is pooled0.

## Execution discipline

- construction: one fresh case per arm, excluded;
- formal: exactly one invocation;
- raw stdout retained before parsing;
- parser consumed only the suffix beginning at the first JSON object boundary;
- formal reruns0 / replacements0 / tuning0.

Raw/source hashes:
- runner.py SHA-256: `336b9d5b1cda66df1b0a9bf1fb28713ed5045e17bedcb49bbbbcda97e7f87eae`
- FORMAL.raw SHA-256: `13833ad76a66dfd876c74b91bcee5a86130f0dcde1a5c859a058df2e449d804e`
- parsed FORMAL.json SHA-256: `6aaa93109d7e8f72eeb796482ae2e5f142921b8173e796a7edab55d89eefa197`
- AUDIT.json SHA-256: `14f86b985fe974658c574dc4deb4fa733272bb400ebde96fae5722acf6cbc640`
- CORRUPTION.json SHA-256: `ce0254c42bf00a47a27ecc32dbb45c4f39f3567e11a1a65353edf1c4023a2c90`

## Formal first outcome

Disposition: `PASS_DYNAMIC_FOCUS_FOOTPRINT_X11_A2_SCOPED`.

All four arms completed 6/6:
- STATIC_SUPERSET + alternate-window tail: exact X red / Y blue.
- RESOLVED_BOUND + alternate-window overlap: exact X red / Y blue.
- RESOLVED_BOUND + focus change: focus mutation serialized until after A effect; X remains red.
- RESOLVED_UNBOUND_NEGATIVE + focus change: A is redirected to Y red, X remains initial, providing the intended discriminator.

Timing in this synthetic fixture:
- static median both-effects wall: 221.0175675 ms;
- resolved-bound alternate overlap median: 120.498031 ms;
- median difference: 100.5195365 ms (gate >=70 ms).

Independent audit PASS: 10/10 checks, including semantic checks from raw fields, reported-median recomputation and zero residual Xvfb display sockets/locks for the formal display range.
Corruption controls 4/4 rejected.

## Interpretation

The analytical #1742 contract transfers to one live X11 selector: when the dynamic target is chosen from current focus, preserving focus as a read/currentness dependency permits safe overlap with a non-selected surface while forcing serialization of focus mutation. Omitting that selector dependency redirects the delayed effect.

Scope remains narrow: raw X11 focus is not general application object identity, and the synthetic 120ms/100ms tails do not establish production speedup.
