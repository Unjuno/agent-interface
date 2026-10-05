# A05 plan: current-source shared-display one-key `up_batch`

A05 is the current-source successor to A04, whose final pre-candidate gate stopped on a source-ref mismatch. It tests one-key `up_batch` calls through the exact PR #7974 V4/V3/V12 chain on a shared private Xvfb server. This is not a replay of A03 or A04: A03 exercised single-key `up`; A04 never started; A05 uses the newly observed current source and operation path.

## H / T / D / C / U

- **H:** With two current candidate owners on one Xvfb server, a receipt-verified one-key `up_batch` from owner A makes the server-global W keymap neutral while owner B's process-local state still lists W as held.
- **T:** One candidate invocation on private display `:95`. Run a single-owner down/one-key-up_batch control, then two independent owners with distinct leases: both admit W, A performs `up_batch(['W'])`, an independent Xlib observer samples global state and the candidate queries B's local `input_state`, then B performs the same one-key batch and final state is sampled. No game, GUI, physical input, model, or user display is involved.
- **D:** Confirm only if control is false/true/false with one verified batch receipt; pair is false/true/true/false/false; owners and leases are distinct; A's receipt is verified while B still lists the W keycode; B's receipt is verified; final global state is neutral; cleanup errors are empty. Preserve any first STOP or mismatch; no retry.
- **C:** XTest release and XQueryKeymap refer to X-server/device state, while each owner's held inventory is process-local. One-key `up_batch` verifies the current batch API path, not ordering across multiple keys.
- **U:** One private Xvfb server, one key and one-key batches. No production display arbitration, physical state, app/game delivery, useful feedback, bounded recovery, threat response or MAP01 outcome is established.
