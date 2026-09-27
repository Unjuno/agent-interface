# Native partial-execution failure regression

2026-09-19. Seven existing/private-Xvfb integration tests passed, including a new
fault after an actual native left-button press. The faulting program returned
`execution_failed`, completed operations `[0,1]` (focus and move), failed
operation `2` (press), three emissions (move, press, recovery release), verified
empty buttons, and no saved effect. Later text/save operations were not run.

This is an automated native failure regression, not primary-model visual
self-use, a performance comparison or implementation of visual target guards.
The purpose is to keep already executed actions observable when a future guard
or another runtime failure stops execution. The failed operation remains marked
uncertain even when the injected test knows it emitted a press.

`test.stderr` retains the seven-test result; `source/` retains the implementation
and tests. Separate local unit tests exercise partial text, earlier observations,
release failure and close failure through the common result adapter. The focused
unit suite passed 32 tests. The live fixture's temporary files were removed by
the test suite; there is no retained frame or raw per-program JSON from this run.
`driver.py` and `cleanup.json` record the private Xvfb launch and termination.
The dependencies were supplied through the local Tk extraction documented in
`../native-result-self-use-01/README.md`. `SHA256.json` covers retained files
except itself and this README. CI runs the new native and partial-failure tests.
