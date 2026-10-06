# V12 cleanup-measurement repair review

Read-only technical review of the three uncommitted files in `work/perkey-owner-guard-repo-e0cc-20261005`. I did not rerun tests or edit production/tests. This is not a quorum vote.

## Source review

I found no material defect in the new local bracket construction. When measurement is enabled, `release_key` timestamps and retains the pre-sample already used to decide whether to issue KeyRelease, plus the post-sample already used to decide whether to retry. Each retry's post-sample becomes the next attempt's pre-sample, so the published cleanup bracket uses the original first pre-state and the final post-state. No extra `query_keymap` call is added. With measurement disabled, the additional timestamps and per-attempt sample dictionaries are not made; the test also checks the existing three cleanup keymap calls remain three.

The `KeyEdgeMeasurements.edge(..., cleanup=True)` call uses the saved active `(key, token, actuation_id)` entry and requires the final physical state to be up, successful release/sync operations, and the existing valid endpoint samples/timestamps. The identity is consumed by `edge`, and the later `clear()` retires any remaining/unconfirmed entries before aggregate pointer/state verification. This keeps a partial cleanup honest: a confirmed earlier key can retain its UP bracket even when a later key remains down; the later key is unconfirmed and the existing release-pending fence prevents new actuation. No cleanup row is promoted to an ordinary batched-UP receipt, and the generated fields continue to set input authority and application-consumption observation false.

The added cases cover two-key identity retention, repeat cleanup without a second edge, retry sample custody, unknown initial sample, already-up/no-attempt behavior, partial persistent loss and input fencing, and measurement-off/on query counts. The recorded test result from the task owner is 9 passing tests against 7 baseline failures; I did not independently rerun it.

## Remaining integration boundary

This source patch stores the new measurements under `owner_release.key_release_attempts[code].physical_key_measurement`. Current V4 only joins `owner_explicit_keyup` rows for explicit UP, and V3's terminal cleanup validation checks `owner_release` verification/state but does not publish nested per-key cleanup measurements as their own rows. Therefore this patch repairs the owner-local receipt, but an actual V39/child propagation test is still needed before claiming the cleanup bracket reaches the retained event stream or a V39 projection. Keep cleanup evidence distinct from ordinary release-pair acceptance.

The ledger still stores `(key, token, actuation_id)` without V39 `(id, step)` context. A bridge can potentially join through its own held-key map, but that join must be exact and tested on cancel/expiry/focus cleanup; the owner record alone does not currently carry that program/step attribution.

The parent is separately strengthening watchdog-triggered expiry/focus schedules and checking real child transmission. Those are the right remaining checks; source-level verification here does not establish end-to-end emission, live input, application consumption, or task effect.
