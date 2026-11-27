# A09 preregistration — current-main V39 owner close on isolated Xvfb

**H.** The exact current-main V12 owner composed through V4→V3, after one `a` key is admitted to a focused Xvfb client, will deliver a matching KeyRelease when the V4 wrapper closes, record one verified empty `owner_release(reason=close)` with the matching intent token and keycode receipt, and stop the owner thread.

**T.** Freeze the four owner source files from current main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. Build a no-network-at-run WSLc image from the locally cached, digest-pinned Python base; install isolated Xvfb and Python-Xlib dependencies at build time. Launch one TCP-disabled Xvfb display `:131`, map and focus one window, call down once through V4, observe KeyPress, call `close()`, then observe KeyRelease and observer keymap-up. Preserve raw events, exact source/image identities, cleanup state and exit status. A raw-only auditor validates the owner record against the client events and the freeze.

**D.** `PASS_METHOD_SCOPED` requires exact current-main source hashes, one accepted key admission (`a`) with an intent token and keycode, a same-key/same-window KeyPress then KeyRelease in timestamp order, server key-up, exactly one matching verified empty close receipt including the per-key release attempt, a closed/stopped owner with no live thread, and Xvfb exit 0. A contradictory complete result is FAIL; setup, incomplete run or cleanup uncertainty is STOP. Candidate executes once; auditor executes once if raw exists; no retry or overwrite.

**C.** This is a new source-lineage check after A08: current main added admission keycode/intent identity fields and changed V3 cleanup reconciliation. It is one synthetic X-server run, with no game, model, physical keyboard, real desktop app, or task outcome. It does not repeat A08's consumed run or claim physical release.

**U.** Whether the updated current-main V12/V4→V3 composition preserves the A08 close-path behavior is unknown until this single run. Physical input, desktop/game delivery, reliability rates, latency under load and Issue #59 completion remain untested.

The only output leaf is `results/A09/`; it must be absent before the candidate. No candidate result may be overwritten or rerun.
