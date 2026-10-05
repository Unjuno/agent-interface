# V12 cleanup repair follow-up review

This is an additive follow-up to `peer-repair-review.md`; v1 is preserved unchanged. Read-only review of the additional `last_cleanup` cause propagation in `input_owner_v12.py` and its focused tests. No tests or source were rerun/edited here; this is not a quorum vote.

## Cause propagation

The new path is narrowly keyed by Python object identity. On `up_batch`, if the active lease does not match, the code maps a cause only when `active is None`, `last_cleanup` exists, and `last_cleanup[0] is lease`. A same-token but distinct lease still reaches `ValueError`. The tests exercise this, and also verify an old canceled lease cannot up-batch against a fresh active hold.

`last_cleanup` is written only at the successful end of `release(reason)`, after neutral verification succeeds and while the just-cleaned lease is still in `active`. The failed-verification branch raises before that assignment; the watchdog then clears `active`, while `release_pending` remains set. The request-loop gate rejects `up_batch` while `release_pending`, so an unverified cleanup cannot use the remembered-cause mapping. A new accepted key DOWN clears the remembered cleanup before establishing the new active hold. The typed mapping is restricted to the recorded reason: cancelled→`Cancelled`, expired→`Expired`, focus/surface change→`DecisionRequired`; other verified cleanup reasons retain the prior `ValueError` behavior. I found no route in this diff that maps a failed release or a different lease to typed cancellation.

These checks address the reproduced cleanup-first shim sequence: after the watchdog already released and verified the key, the caller's delayed same-lease `up_batch` receives the original interruption instead of a spurious `ValueError` or a second input operation. The exact-object guard does not create an explicit-UP receipt or issue display I/O.

## Evidence boundary update

The parent reports that full01 confirms the cleanup owner record reaches both `input_released.owner_release` and `terminal.interruption.record`, joined by owner, intent, key, and actuation ID. Given that retained child result, a separate bridge event is not required for this path; the existing transport preserves the owner record. That resolves the propagation concern stated in v1 for the exercised full01 route. This follow-up source review does not independently audit full01 bytes, and full02 remains separate evidence.

The focused unit tests include watchdog-record synchronization for cancel, expiry, and focus paths, plus no-I/O checks on late batches, a same-token different-object control, and an old-lease/new-hold control. Root reports the 47-test combined suite passed and is checking full02. Those run outcomes were not independently rerun here.

## Independent retained-raw spot check

I read only the retained `full02`, `full03`, and `full04` files under this job, without rerunning the child or controller. For full02 (`hard_change`, child exit 0), typed health sequence 10 is observed at 60. Its `cover-1/a` cleanup UP has `CONFIRMED_PHYSICAL_UP`, `identity_status=RETIRED`, pre-down true/post-down false, and the same `owner_id`, `intent_token`, `key`, and `actuation_id` as that key's earlier admission. The bracket is `[756927616750, 756927904458]`; owner verification is 756928037125, `input_released` publication is 756928274791, cancellation terminal is 756929301458, and turn-3 model begin is 756970172916, in that order.

For full03 (`unknown_change`, child exit 0), typed health sequence 10 is unknown. The corresponding cleanup UP has the same exact four-field admission identity join and a confirmed down-to-up keymap bracket `[801201219791, 801201534583]`. Owner verification (801201788000) precedes `input_released` publication (801202075333), cancellation terminal (801203589958), and turn-3 model begin (801256332458). In both successful cases, the same nested cleanup owner record and measurement appear in `input_released.owner_release` and `terminal.interruption.record`; neither grants input authority nor claims application consumption.

For full04 (`failed_release`, child exit 1), the saved per-key measurement stays `KEYMAP_EDGE_UNCONFIRMED`, has no bracket or actuation ID, and both endpoint samples remain down. The stream emits `input_release_unverified`; it does not emit successful `input_released`, the terminal is failed with an unverified interruption, and no turn-3 model begin occurs. This is the expected fail-closed case, not evidence of a successful release.

These checks support the exact saved fake-environment scenarios and their retained child event flow. They do not establish real X-server or application consumption, and do not change the source-review conclusion about the narrow scope of the last-cleanup cause mapping.

No finding from this bounded diff review. The claim remains limited to the exact recorded lease cause after verified owner cleanup; it does not establish physical application consumption or task effect.
