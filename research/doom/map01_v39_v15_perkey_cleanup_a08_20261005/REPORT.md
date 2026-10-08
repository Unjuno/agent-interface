# A08 result — synthetic retry recovered

Frozen candidate ran exactly once under bundled host Python 3.12.14. The independent auditor ran once and passed **32/32** checks, including the candidate/source-manifest freeze hashes and all 21 current-main source copies.

The normal arm completed with one per-key release attempt; its fake-server sample was neutral. The injected-loss arm dropped exactly its first fake KeyRelease, recorded the key down after attempt one, recorded it neutral after attempt two, and completed with a verified terminal release. Both transitions explicitly report `physical_verification_authoritative: false`.

A07 remains preserved as a setup STOP: its V13-generated lease lacked the fake session's observed-focus value. A08 supplies fake focus 41 from the test action-loop boundary, matching the fixture's fixed focus. The production owner, executor, and release-composition files remain source-pinned and unmodified.

**Scope:** host-run synthetic fake-X composition only. The host network was not sandboxed, although the candidate makes no network calls. No container, real X11, GUI, Doom, model, physical keyboard, OS input, application effect, threat response, useful feedback, recovery efficacy, latency, or MAP01 result is established. This does not meet the separately gated fresh live-exposure requirement for Issue #59.
