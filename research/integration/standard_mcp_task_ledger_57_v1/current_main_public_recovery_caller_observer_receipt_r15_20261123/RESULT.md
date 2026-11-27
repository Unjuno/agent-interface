# R15 — public compiled-caller Fake observer receipts

## Result

One normal and one `-O` run of the public compiled-caller recovery/task-oracle test both passed (1/1 each; exit 0). The test retained its prior exact-result, source-action UNKNOWN, separate recovery release/horizon, independent fixture oracle success, and no-replay assertions. Added Fake callback receipts include observation identity and timing; their count and IDs match public observation receipts exactly. A fail-closed lower `open_session` guard remained untouched, and accepted API Futures/reports drained before server close.

## Scope and limits

This establishes observer attribution and synthetic composition for the selected test path only. It does not prove the historical R10 orphan mechanism, live Win32 task effect, recovery reliability, efficiency, MAP01, Research Preview, or distributable-runtime behavior. Full frozen conditions and raw runs are in this directory; SHA-256 manifest covers the packet.
