# Current-v39 owner keymap witness construction control

## H / T / D / C / U

- **H:** The v39 typed release adapter can be exercised with the current-main `input_owner_v10` source and a private Xvfb so two distinct W-key down/up occurrences each have matching backend admission/release telemetry and before/down/up XQueryKeymap witnesses.
- **T:** Use exact snapshots of the current-main InputOwner v10, the candidate v39 typed release backend from PR #7355's current head, and the transition wrapper from PR #7376's current head. Run two key cycles on a fresh private TCP-disabled Xvfb, with the v10 owner release boundary after each raw key-up. The backend's `raw()` method and real InputOwner thread are exercised; each occurrence explicitly closes its owner lease after raw key-up, matching the executor lifecycle boundary; the backend base initializer is stubbed to avoid loading Doom/application dependencies. An independent standard-library auditor checks all raw receipts and keymap bitmaps.
- **D:** Pass only if both unique intent tokens have one admission and one release receipt; each occurrence's server keymap is false/true/false at pre/down/up; receipts are ordinary, ordered, owner-matched, fail-closed authority-wise, and the close record verifies empty owner state; private Xvfb exits and removes its socket/lock.
- **C:** XQueryKeymap is virtual server state. This test does not use a game, application, physical keyboard, model, GPU, or task scoring. The base hold sequence is bypassed with a stub; the actual backend raw method, current-main owner source, and transition wrapper are loaded.
- **U:** This is a two-occurrence Xvfb construction measurement, not physical input, application consumption, useful feedback, bounded recovery, latency, task effect, safety, or threat exposure. Candidate performs no network calls; Xvfb disables TCP. The guest cannot create a network namespace (`unshare -n` preflight failed), so the environment is not network-isolated.

The stopped formal candidate allocation `MAP01-V39-RELEASE-TELEMETRY-LIVE-59-T0-20261004-01` is untouched. This control has a new construction ID and output path.
