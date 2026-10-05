# A04 plan: exercise current V15 owner `up_batch` on a shared X server

Issue #59 / PR #7974 review evidence. A04 is a separately frozen operation-path successor to A03, not a rerun. It tests one-key `up_batch` calls through the current V4/V3/V12 owner composition; it does not instantiate the complete V15 multi-key release-batch backend.

## H / T / D / C / U

- **H:** With two current candidate owners on one Xvfb server, a receipt-verified one-key `up_batch` from owner A will make the server-global W keymap neutral while owner B's process-local bookkeeping still lists W as held.
- **T:** One candidate invocation on private display `:96`, with exact PR #7974 sources frozen in `FREEZE.json`. Run a single-owner down/one-key-up_batch control. Then create two independent owner instances with distinct leases, admit W under A and B, sample the server keymap after each down, call A's `up_batch` for `['W']`, sample server state and B's `input_state`, then call B's `up_batch` and sample again. The observer is a third Xlib connection. No game, GUI application, physical input, model, or user display is involved.
- **D:** Confirm only if control samples are false/true/false and its one-item batch receipt is verified; pair samples are false/true/true/false/false; A and B have distinct owner IDs and lease tokens; A's one-item receipt is verified while B still lists the keycode locally; B's one-item receipt is verified; final server state is neutral; cleanup errors are empty. Any setup STOP or complete-run mismatch is retained with no retry.
- **C:** XTest KeyRelease and XQueryKeymap operate on X-server/device state; each owner's held-key inventory is local state. A single-key batch call on two owners tests this cross-owner relation, not multi-key batch ordering.
- **U:** One private Xvfb server and a single-key batch API call. This does not prove production Xorg/Wayland behavior, physical key state, app/game delivery, cross-process allocation enforcement, useful feedback, bounded recovery, threat response, or MAP01 outcome.

## Frozen identities

- Current main: `ff677c7fc04ba72923ee375527ae39489728a0bd`.
- Candidate source: PR #7974 head `2a79899f41bf71ab41df8dd5dcf1cd9e70f9eca8`.
- Output: `results/A04/`; one candidate invocation maximum; auditor runs once only after candidate exit 0. No candidate/auditor retry.
