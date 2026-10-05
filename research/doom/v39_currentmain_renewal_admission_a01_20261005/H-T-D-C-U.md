# Current-main V39 renewal-admission repair

## H — Hypothesis

For V39 on main `2f2c83c3da36566bac410b13b2ed5202c9641f1a`, a soft observation can advance the latest sequence after the controller prepares a cover renewal but before executor admission. The executor's exact stale-sequence rejection means that renewal never became active. Treating it as a terminal controller error abandons the pending planner turn and leaves cleanup incomplete. The repaired component should retain the previous verified terminal, represent the rejected renewal as unadmitted, and keep observing while the planner finishes. A hard validity event must still interrupt the planner; any other rejection must still fail closed.

## T — Test

Freeze the exact current-main controller, repaired candidate and focused regression suite. Extract the controller's actual `wait` and `submit_cover` closures into a stdlib-only harness with a deterministic event queue. Run four cases: accepted admission, soft observation followed by the exact stale rejection, unexpected rejection, and coverless soft/hard observations. Run normally and with `python -O`. Also run the existing wait regression suite under both modes. Attempt the broader V39 controller suite once to identify dependency availability; do not substitute a stubbed-import result.

## D — Decision

Scoped PASS requires the exact soft observation sequence to become `latest`, the renewal rejection to classify as unadmitted with no cover ID, accepted admission to remain accepted, unexpected rejection to raise, soft events to leave the planner uninterrupted while coverless, hard invalidation to request interruption, and both focused suites to pass in normal and optimized Python. Any broken assertion is FAIL. Missing Pillow for the broader suite is HOLD for that suite and does not change focused results.

## C — Counterexamples and alternatives

An observation during admission may represent a hard policy change rather than harmless soft drift; therefore submission waits use the validity monitor, and the coverless wait continues the same monitor. Executor admission semantics may change the exact rejection reason; unrecognized responses intentionally fail closed. A passing extracted-closure test does not execute the entire planner loop, actual executor process, game, UI, physical input, scorer, or cleanup boundary.

## U — Limits

This is a local code-level component/integration regression on macOS arm64 with Python 3.12.13. No model, game, GUI, executor session, live input, container, GPU, formal allocation, task effect, or MAP01 outcome was run. The existing full controller suite could not import because Pillow is absent; full runtime integration, release verification, reaction bounds, threat response, recovery, and gameplay remain unverified.
