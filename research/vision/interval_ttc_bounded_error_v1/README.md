# Bounded-error interval TTC (Issue #8157)

Construction A01 and A02 and the one-shot formal protocol live here. A01 used a pinned Python OCI image in WSL Arch + Podman and ran five arithmetic/fail-closed tests; A02 construction ran eight tests in the same pinned arm64 image through this Mac's OrbStack-compatible runtime. Neither construction stage was a corpus run. Formal details are frozen in `PROTOCOL_A02.md`. The formal allocation has not been invoked unless `results/FORMAL_A02/RUN_RECORD.json` says so.

Only finite synthetic radius traces are in scope. The candidate receives public timestamp/radius/bound/track histories. Truth, strata, split, and hazard labels stay in the auditor-only oracle. There is no GUI, game, model, user data, input, actuation, or runtime integration. A passing result cannot establish scene semantics or safety.

## Preserved formal and posthoc outcomes

- A02 ran once and remains `FAIL_METHOD` under its integrity gate; the scientific score was originally unscorable after 98 occlusion-prefix reconstruction mismatches.
- A03 remains `STOP_AUDITOR_RUNTIME_ERROR`. A04 remains `PASS_RAW_RECONCILIATION_ONLY`: it reconciled all 2,400 prefixes and attributed the A02 mismatch to future-history handling, but did not adjudicate score gates.
- A05 stopped before reading inputs on an argument/root mismatch. A06 stopped before input read on a freeze-schema mismatch. A07 read the pinned inputs and reconstructed them, but its calibration-threshold and paired-lead mutation controls failed; its score is unusable.
- A08 independently reconstructed the same pinned inputs with zero errors and passed all six mutation controls. Its posthoc diagnostic is `NO_INCREMENTAL_VALUE_SIGNAL_ON_RETAINED_A02_RAW`: numeric interval coverage is 87–92% across the four in-model profiles with no containment misses, but neither method yields on any eligible evaluation hazard, and there is no strict false-yield reduction in iid, correlated, or irregular/dropout profiles. This does not change A02's formal `FAIL_METHOD` or constitute a method pass.

See `FREEZE_A08_LOCAL.json` and `results/POSTHOC_A08_LOCAL_DECISION_AUDIT/` for exact hashes, per-profile counts, and the local one-shot audit record. No A02 candidate, generator, prior auditor, container, or runtime was rerun for A08.
