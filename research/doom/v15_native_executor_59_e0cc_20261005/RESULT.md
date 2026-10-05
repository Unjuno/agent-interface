# Native V15 Executor composition: behavior witnessed; frozen audit FAIL retained

One ordinary construction invocation ran on 2026-10-05 at 12:47:35–12:47:36 UTC on the owned Debian12 arm64/Xvfb VM. The actual measured V15 Backend and ExecutorV13 executed three sequential programs through `submit` and production `execute`, including real snapshot/ImageGrab/encoder/decoder publication. Driver exit was 0. The frozen independent raw auditor returned **FAIL_NATIVE_EXECUTOR_COMPOSITION_SCOPED, 337/338**; its sole failed predicate was `only_loopback`. That result has not been rewritten or promoted to a complete PASS.

| Program | Native recipient events | Terminal | Observed boundary |
|---|---|---|---|
| Normal hold | DOWN a/s/w, UP a/w/s | completed, one step | Three unique matching admission/release identities; complete batch order equals native UP order |
| Cancelled hold | DOWN a/s, UP a/s | cancelled, zero steps | Independent keymap confirms both down before cancel; verified input_released precedes incomplete late-UP rows and cancelled terminal |
| Fresh follow-on hold | DOWN w, UP w | completed, one step | Same backend/executor, new token and actuation after cancelled worker join and inactive slot |

All terminals have verified empty keys/buttons, the independent final keymap is neutral, and there are no trailing native key events. The cancellation record contains the two matching `per_key_cleanup_snapshot` UP measurements. The late UP rows remain incomplete and nonauthoritative. There are 16 exact typed/full observation epochs with matching saved PNG RGB hashes; the health/ammo readers deliberately return UNKNOWN. This proves no game HUD accuracy or useful task effect.

Production hold releases its held set in enumeration order; the normal observed a/w/s order is not a guarantee of reverse DOWN order. The pre-freeze draft's reverse-order assumption was corrected before invocation and remains in PROTOCOL.pre-freeze.md.

## First audit failure and diagnosis

The driver captured effective CPU/memory/swap/task limits as 100000/100000,1073741824,0,64 and only the interface names from its private network namespace. They were `lo`, `tunl0`, `sit0`, and `ip6tnl0`, so the frozen name-only `only_loopback` predicate failed. That raw lacks flags, addresses, and routes; it cannot establish whether the extra interfaces supplied connectivity. PrivateNetwork configuration is not substituted for that missing observation.

A separate **no-input infrastructure diagnostic in a new namespace**, after preserving the first audit, found the same three extra interfaces DOWN, without addresses or routes; all reported routes belonged to lo. This supports revising a future collector to retain flags/addresses/routes instead of accepting or rejecting names alone. It does not reconstruct the original namespace or cure the frozen failure. The first diagnostic itself failed while reading /proc/1/ns/net as study; that PermissionError is retained. A second diagnostic omitted that inaccessible comparison and recorded the link/address/route state. No privilege bypass, network connectivity attempt, Xvfb, or candidate replay occurred in either diagnostic.

The eight corruption transformations were fixed before the candidate, but the original control runner would have counted any pre-existing failure as a rejection. It was therefore **not invoked**. An additive post-run diagnostic version retains the same eight mutations, synchronizes duplicated event views, and requires additional semantic failures beyond baseline `{only_loopback}`. It rejects **8/8**: missing normal UP, wrong release token, nonempty cancelled terminal, follow-on before cancelled terminal, missing early release, wrong native UP order, wrong capture epoch, and missing native DOWN witness. This does not turn the original audit into PASS.

## Provenance and teardown

- Source: `daa156edd8df541dfe0192c3f6f0c69b36b92fa2`; all 81 exported Git images match before and after; 39 loaded module hashes match. The 81 images also match the clean virtual merge with main `307b9e2f0420f130e9d933c037cac78501d2e547`, tree `f174a0a31d76ffcf578f1a5a00c1173d4fdd3c46`. This is selected source applicability, not full-PR review.
- Raw SHA256: `6d7b7acc4fcbb5b5b01e10affbd2e55711549819309f13b01d4460858550cd21`.
- Candidate source, saved-only auditor, initial corruption driver, protocol, source lock, environment and launcher are hash-fixed in freeze.json before invocation. The candidate ran once; no native rerun.
- Driver author: existing /root/bugbot; independent auditor: /root. The peer separately checked retained raw, source joins and teardown; this is technical verification, not nonauthor merge quorum.
- Owner stopped, owner and executor watcher threads are no longer alive; observer/session connections closed; window destroyed; Xvfb exited 0. Host-side guest readback found no Xvfb process and the unit inactive, with the same raw hash and 81/81 source hashes. The owned VM was stopped and preserved.
- A pre-run peer claim about the terminal release shape was rejected after actual import-only MRO inspection: `session_v5.release_all` returns the current owner's full record. Strict empty-button validation was retained.

## Scope and next gate

This adds the **native production execute/lease/terminal boundary** absent from the preceding direct-raw native probe. It does not run the V39 controller, actual Session launcher/stdin child, a game, model, physical keyboard, threat exposure, useful application feedback, bounded task recovery, Windows or a matched performance comparison. A new program after cancellation is a lifecycle witness, not general recovery efficacy. One native scheduling realization does not quantify the cancellation race.

Future native protocol: collect interface flags/addresses/routes prospectively and use a predeclared network predicate that distinguishes inactive tunnel templates from configured connectivity. Keep this first FAIL unchanged; do not rerun merely to repaint it green. The separately gated #59 live-game allocation remains unassigned under inspected r139. No runtime source is changed here, no main ref was updated, and #59/the computer-control objective remain open.
