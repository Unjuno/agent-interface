# Issue #5970 T2 — prospective causal provenance on isolated X11

## H / T / D / C / U

- **H:** A serialized, explicitly armed XTest event can be observed by the independent X11 observer and the Tk application with one shared actuation parent ID, distinct source-local event IDs/sequences, and no reliance on timestamps to manufacture causality. A missing or mismatched stream record must fail closed.
- **T2:** Starting from the hash-pinned #4135 X11/Tk source archived at source commit `7625a3fc99f1da2099dc6e20e67383ee88c7f337`, run an additive instrumented copy under a fresh isolated Xvfb display. Before each synthetic Shift press/release, arm both consumers with a fresh ID and wait for both arm acknowledgements. Dispatch the XTest event only after both acknowledgements. Retain raw per-stream records and dispatch receipts. No formal #4135 allocation, user desktop, network, model, or external app is used.
- **D:** `PASS_PROSPECTIVE_CAUSAL_IDS` only if both press and release each produce exactly one app and observer event with the dispatch's shared causal parent, matching key type/detail/X time, distinct strictly increasing local sequences, two prior arm acknowledgements, and a verified neutral terminal keymap. Otherwise `HOLD` for incomplete provenance or `FAIL` for contradictory/misbound records. Independently reconstruct the decision from raw files.
- **C:** This test deliberately serializes one in-flight event and uses a pre-event arm/ack protocol. It validates a controlled fixture's traceability path, not arbitrary simultaneous input, scheduler/reordering behavior, logger overhead, production instrumentation, authorization, or task benefit. Docker Desktop's Linux engine is unavailable; WSL2 Ubuntu's installed Xvfb/Tk/python-xlib are the isolated fallback, with the environment explicitly recorded.
- **U:** Whether production observer/app boundaries can share a trustworthy actuator-issued parent ID without a serialized side channel; how the instrumentation behaves under concurrent or unsolicited input; its latency/storage cost; and whether causal completeness improves any real recovery decision remain unknown.

## Isolation and no-retry rule

This is a new, additive instrumentation probe—not a rerun or regrade of Issue #4135's consumed formal matrix. Use a new Xvfb display and a fresh temporary Tk fixture. The Shift tap must end neutral; terminate only child processes created by this runner. Candidate and independent auditor each execute once. If the isolated display or dependencies are unavailable, record STOP/HOLD and do not retry the live allocation.
