# A03/A04 outcomes

## A03 — construction STOP

`STOP_CONSTRUCTION_RUNNER_ROOT_LAYOUT`. The pinned container image launched, but the package-only `/work` bind did not satisfy the runner's repository-root calculation (`HERE.parents[2]`). Runner exited 1 before loading the candidate path; candidate executions=0. Exact command and traceback are retained in `STOP_A03.txt`. A03 is not retried.

## A04 — current-owner pending-expiry probe

`PASS_CURRENT_OWNER_PENDING_EXPIRY_RECEIPT_SCOPED`. A04 is a distinct run ID with the same frozen scientific source and a corrected repository-root mount. Its no-input container preflight passed; the candidate ran once in the immutable `python:3.12.11-slim` arm64 image with networking disabled. The independent raw-only audit confirms: one context/actuation-bound F8 down; execute-exit drain cursor remained zero while owner cleanup had not yet published a record; one owner-confirmed physical-up record appeared after unblocking; the bridge emitted exactly one matching `input_release_measurement` before the single `expired` terminal; owner/fake/bridge states were verified empty.

This establishes that the `release_all()`-finally drain probe carries the late receipt for this one forced schedule with PR #7805's latest frozen owner v13 candidate blob `123cd29…` and bridge v2 blob `ee1220…`. It does not validate live X11, actual game/task effect, independently useful feedback, bounded recovery, threat control, timing distributions, production integration, or Issue #59 completion. The A03 wrapper STOP and A04 scoped PASS are separate outcomes; no resource-limit enforcement claim is made from Docker options.

Raw candidate/audit are under `results/formal_02/`. Source, image, command, and output identities are in `SOURCE_LOCK.json` and `RUN.json`.
