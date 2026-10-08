# Caps Lock check-to-XTEST successor (#8328), protocol v2 draft

This additive protocol follows the v1 allocation, which stopped at `C01` because the raw event auditor incorrectly treated the Shift modifier KeyPress with an empty character as a payload character. The complete v1 allocation record and STOP audit remain immutable at `../caps_text_check_to_xtest_successor_v1/formal_runs/run_20261008_a01/`. No guard-arm case ran in v1.

## Current status

`FREEZE.json` is deliberately marked `PROTOCOL_DRAFT_NOT_ALLOCATED`. The revised event contract checks payload characters from nonempty `KeyPress.char` fields and independently balances keycodes across every KeyPress and KeyRelease, including modifier keys. Regression tests use the actual stopped v1 C01 record and verify that a missing modifier release is rejected.

The draft preserves the v1 hypothesis, arms, nine-case order, environment constraints, evidence requirements, and stop-on-first-unexpected rule. It is a separate allocation: no C01 result is carried forward and no v1 case may be rerun under the old freeze. Before any execution, this protocol needs independent review, fresh source-manifest verification, and a new immutable commit read back from GitHub. The runner refuses to execute while the status remains `PROTOCOL_DRAFT_NOT_ALLOCATED`.

## Environment and scope

The earlier study uses a dedicated OrbStack Ubuntu Noble ARM64 VM because the local container content store could not provide a dependable image. Its results are VM/Xvfb evidence, not container replication or product-level computer-control validation. The bounded test covers only the X11 backend, Tk Entry, XKB map, and deterministic Caps Lock interposition. It does not establish behavior across live desktops, applications, layouts, IMEs, physical HID, models, latency, safety, or prevention/recovery correctness.

The production backend remains unchanged. Current-main source identity and all runtime imports remain pinned by `SOURCE_MANIFEST.json`; any source drift before a future allocation must stop the run.
