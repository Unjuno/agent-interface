# Sibling standard-caller Xvfb receipts from run 39620085797

These are artifacts from the sibling `x11-integration` job, not the isolated `prestarted-cancel-xvfb` job. That full X11 job completed successfully: 77 Xvfb tests and 5 server-stop/recovery tests passed after test code began separating the bounded cancel response from the terminal cancellation receipt. The isolated supervisor job in the same workflow failed separately; see the parent packet.

## Blocked owner I/O with responsive Xvfb

`blocked-release/raw.json` preserves a standard-caller scenario where the owned client was blocked in real Python-Xlib `Display.sync`, while the separate cleanup path retired the owner, observed XRes disconnection, and released the held key. An independent parent X client read both `a` and `b` up at release and again 8.501 s after cancellation; the delayed `b` press was not observed. The independent synthetic application oracle passed `[1]` initial/final effect and both all-up readbacks. Runtime classification correctly stayed `cancel_unconfirmed` / cleanup UNKNOWN, `release_confirmed=false`, `task_success=null`, replay denied.

Measured values: `interface_guarded_cancel` returned a retained `pending` response after 940.909 ms, exceeding the provisional 300 ms caller-response target but within the scenario's 3 s ceiling. Terminal cancellation completed 922.812 ms after admission. The independent release readback was recorded 857.330 ms after admission, with 589.144 ms attributed to the release worker. This is one scoped trial on responsive private Xvfb, through the standard caller, without the opt-in prestarted supervisor. It does not show server-outage release, MAP01, or a population-level bound.

## Whole-server stop

`server-stop/raw.json` preserves a distinct whole-Xvfb-stop schedule. The API returned `pending` in 301.817 ms, before the exact server was resumed. During that interval cleanup remained UNKNOWN with no replay. After resumption, a fresh independent readback saw both keys up at the later horizon, but the immediately-after-resume release readback still had `a` down; the original task oracle therefore failed. The later fresh-target recovery is a separate event; the original held-input task is not scored as success. This does not prove release while the server was unavailable.

The successful test-job conclusion indicates assertions passed, not that each scientific task oracle passed. Keep the per-scenario oracle classifications above.
