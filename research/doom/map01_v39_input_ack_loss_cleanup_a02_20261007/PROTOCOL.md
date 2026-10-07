# A02 — delivered KeyPress with lost response, then terminal cleanup

H: When an XTest KeyPress changes fake-server state and then the call raises before the owner RPC acknowledges it, the current V39/V15 executor path will fail the action, invoke terminal owner cleanup, observe an empty fake keymap, and report a verified release before terminal.

T: Two fresh child processes, one normal F8 down/up and one injected first-KeyPress delivery followed by `OSError`. Each loads the same frozen 21-file current-main V39/ExecutorV13/V4→V3→V12 source closure. Only the fake X provider fault differs. Record requests, owner receipts/releases, terminal state and final fake keymap.

D: PASS_SCOPED if the normal arm completes one step and verifies empty input; the treatment arm terminates failed before step completion, shows one delivered KeyPress and no explicit up-batch receipt, then records a terminal owner release with empty fake state before terminal. FAIL if treatment reports completed or verified while fake input remains down. STOP for setup/observation/result-capture failures.

C: Deterministic in-process fake X; no server transport, competing clients, device state or app consumption. A test-only action-loop/session seam is used; ExecutorV13 and selected release/owner composition remain frozen production code.

U: Construction evidence only; no real X11, desktop, Doom, model, physical keyboard, useful feedback, recovery efficacy, latency or task success.
