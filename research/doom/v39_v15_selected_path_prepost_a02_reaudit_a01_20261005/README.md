# V39/V15 paired keymap A02 — raw-trace reanalysis

This package resolves the audit-shape ambiguity in the preserved synthetic A02 run without changing or rerunning that candidate. The original A02 candidate output and its failed 21/32 audit are retained byte-for-byte. Input verification matched all 23 entries in the original package checksum manifest.

A new raw-only audit A01 first failed 34/35 because it repeated the original class of mistake: it required an explicit nested `route.authority_claims` object that the candidate never emitted. That failure is preserved. A02 changed that check to inspect the actual four `input_release_transition` rows. It passed 35/35 against the immutable candidate trace.

The trace supports a narrow synthetic result:

- In both cases, SPACE (65) and F8 (74) were down at the pre-sample.
- The normal case delivered both UP attempts and sampled no keys down afterward.
- In the injected lost-SPACE case, the SPACE UP was suppressed, F8 was delivered, and the post-sample retained only keycode 65. Terminal cleanup failed closed and reported key 65 still down.
- The pre/post keymap calls bracket the two UPs; there is no query between UP attempts. Per-key release telemetry follows the post-sample.

The separate timing reconstruction joins each candidate admission/ack record to its owner-thread key-up/XSync receipt by key, owner, and intent. Admission→UP-call-start was 0.0720–0.2236 ms for the normal case and 0.0675–0.2114 ms for the injected-loss case. The UP-call/XSync bracket was 0.0023–0.0044 ms for delivered releases and 0.0037 ms for the suppressed SPACE case.

Those are server-call bounds from candidate-reported monotonic records. The KeyDown event precedes admission telemetry but lacks its own timestamp, so exact key-down duration is unidentified. XSync and fake keymap state do not establish physical release or game consumption.

The next required result remains prospective current-main live evidence: per-key admission/up/release timing, independent useful-feedback onset, and bounded recovery under a matched condition. That live-game allocation remains unassigned; this reanalysis is not a substitute or clearance to run it.

See [PROTOCOL.md](PROTOCOL.md), [AUDIT_V2_PROTOCOL.md](AUDIT_V2_PROTOCOL.md), `results/reaudit-a01/AUDIT.json`, `results/reaudit-a02/AUDIT.json`, and `results/reaudit-a02/TIMING.json`.

The copied source snapshots are compressed byte-for-byte in inputs/pr-7926/source-snapshots.zip; run python verify_inputs.py to check all 23 original manifest entries.
