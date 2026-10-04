# Successor A02 — owner-ledger fail-closed repair

This follows the new partial-release-record behavior in #7805. It tests the remaining consistency hazard on the exact #7805 head `c4e893e8515811c77e21639237f1f2a914d4d88b`: aggregate keymap failure occurs after a confirmed per-key up and the owner has published the partial row, yet stale owner state may still permit more input.

## H/T/D/C/U

**H:** On aggregate-query failure, the #7805 owner still clears its held map and active lease only on the successful aggregate path. It may accept and inject a new key while holding a stale key ledger.

**T:** Inject failure at keymap query 5, after admission and per-key up samples; then immediately request another key with the same lease through the owner queue.

**D:** Baseline is unsafe if the new key request is accepted/injected. Repair passes only if the exception propagates, confirmed-up remains published, owner and bridge held ledgers are empty, active lease is cleared, and a post-error down is rejected before injection. The partial row must remain `verified=false`.

**C:** Candidate commit and ten source/supporting blob identities are pinned in `SOURCE_LOCK.json`; exact frozen source is included. Offline WSLc used the cached pinned Python 3.12 slim image, one CPU, 512 MB, no network. No live GUI/game/OS input was used.

**U:** Deterministic fake-display evidence only; no real X11/game behavior, independently useful feedback, recovery efficacy, live threat response, latency, or MAP01 result. Buttons are outside this probe. WSLc warned that memory is limited without swap because cgroup swap limiting is unavailable.

## Result

A02 RED: the latest #7805 source emitted a confirmed-up receipt and emptied bridge-held state, but owner state still listed keycode 74 and an active lease. A03 RED demonstrated the consequence: key `b` was admitted after the error, fake keycode 98 became down, and owner state listed `[97, 98]`.

The repair copy retires the owner hold at the confirmed per-key up and stores the aggregate-query exception as the owner fault while clearing the active lease. A02 GREEN shows empty owner and bridge ledgers; A03 GREEN rejects key `b` as failed closed without injection. Focused candidate tests pass 11/11 and retained owner compatibility 10/10. `audit.py` independently verifies the pinned source blobs and raw outcomes.

This is a source-level successor candidate, not runtime adoption or a current-main detached composition replay.

## Replay

Unzip at `/src`; run baseline RED with `python3 /src/probe_a03.py`, and repair GREEN with `python3 /src/probe_a03.py /src/repair/input_owner_v13_repair_candidate.py`. The focused and owner-compatibility runners target the repaired copy.
