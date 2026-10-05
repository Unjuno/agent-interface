# V39 shared-display owner-pair Xvfb experiment A01

Issue: #59. This is a bounded construction experiment prompted by the open
PR #7974 review question about two input owners sharing one X server. It does
not consume or substitute for the private live-game allocation.

## H / T / D / C / U

- **H:** Two current candidate V4/V3/V12 owners connected to the same Xvfb
  server can each keep the same key in local held-key bookkeeping, while one
  owner's XTest KeyRelease makes the server-global keymap report that key up
  and gives that owner a key-up receipt marked verified.
- **T:** On a fresh Ubuntu 24.04 arm64 OrbStack VM, run one candidate invocation
  against one private Xvfb display. First run a one-owner W down/up control.
  Then connect two independent owner instances to the same display; use
  separate leases and the same W key; sample `XQueryKeymap` using a third
  connection before and after A's up; read B's local `input_state`; finally
  release B and close both owners. No game, GUI application, physical input,
  model, or user display is involved. Freeze the current PR #7974 sources.
- **D:** Record `CONFIRMED_SHARED_DISPLAY_CROSS_OWNER_RELEASE` iff the control
  yields false/true/false server state and verified receipt, then in the pair
  case A and B both admit W, A's up receipt is X11-keymap verified, the server
  keymap becomes false while B still reports W held, and B's subsequent up is
  also receipt-verified. Any setup/candidate failure is retained STOP; any
  complete-run mismatch is a retained counterexample to H. No retry.
- **C:** XTest KeyRelease is server/device-level behavior; local `held` maps are
  process-local. A separate observer establishes only X server keymap state.
  A single owner on an exclusive display is outside the interference condition.
- **U:** This tests one current owner implementation on one Xvfb server. It
  cannot prove behavior on production Xorg/Wayland, physical key state, GUI or
  game consumption, cross-process allocation policy, threat response, useful
  feedback, bounded recovery, or MAP01 outcome. A confirmed result requires
  exclusive-display/cooperative-arbiter enforcement before interpreting a
  server-global keymap receipt as owner-isolated evidence.

## Frozen identities

- Current main base: `6860b585305e539ec93896f5adcbf658cbbd8592`.
- Candidate source: PR #7974 head `1627581fddb84521e87942cca49ed40310683f65`.
- Output: `results/A01/`; candidate may run once, auditor only after a zero
  candidate exit. Preserve setup, raw output, process status and audit as-is.
- The exact vendored source file hashes and package versions are recorded in
  `FREEZE.json` before VM execution.
