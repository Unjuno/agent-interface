# Native navigation in the six-task assistant workload

The primary assistant used the same six-task Chromium fixture (seed 991083),
viewed the initial and repair native PNGs, and supplied explicit coordinates.
Navigation now dispatches focus, Ctrl+L, URL text, Enter and release through
`runtime.cli_v1.api.dispatch`. Field/Save operations retain the existing native
handle bridge. No research Driver input calls remain in this workload.
Fixture startup still uses the existing setup/session utilities. This is a
research harness, not promotion of the handle bridge into the public API.

## Both attempts

* `run-1`: three exact saves. The fourth navigation program returned completed
  and verified release, but the expected ready window title did not appear
  within ten seconds. No replay occurred. The final failure screen was not
  captured in this attempt, so the precise cause is unknown.
* `run-2`: six exact saves, no duplicate/unexpected submissions; six completed
  navigation programs, twelve completed guarded field/Save programs. Task 4's
  old field was refused with zero input. The assistant viewed source 31,
  repaired both targets, and reused those targets for tasks 5/6. All eighteen
  completed native programs verified empty key/button release.

Between attempts, the harness added explicit 100 ms waits after Ctrl+L and URL
typing, and best-effort error-screen/title retention. This does not prove the
timeout's cause or establish a generally reliable timing policy. Both attempts
terminated all owned processes; Openbox returned 1, Xvfb and Chromium returned 0.

The backend now supports `:` and `/` using the live X keymap's unshifted/Shift
levels. Other supported characters remain letters/digits/space/._-. The whole
text is preflighted before input. This is not full URL syntax, Unicode, arbitrary
XKB groups or modifier-state-independent text entry. The test fixture uses its
default Xvfb keymap with no externally held modifiers.

## Verification and limits

`text-live-test` records eight passing native X11 tests, including exact saved
`http://127.0.0.1:8765/a-._ A` and unsupported-text zero-input refusal.
`unit-tests.txt` records eleven passing focused tests, including shifted URL
symbols and unsupported keymap groups before any prefix emission.
The retention check verified 87 PNG/hash links and 281 manifest files.
`SHA256.json` covers retained data and final-source snapshots, excluding itself
and this README. Original artifact paths identify the run environment; images
are copied unchanged under each run's `bridge/images` directory.

Final-source snapshots describe run 2. Run 1 used the same backend changes but
did not include the two navigation waits or the later error-capture block.
Navigation programs retained per attempt specify their actual executed ops.

Successful-run navigation took 535–604 ms including native observation, dispatch,
readiness-title polling and the rendering allowance. Guarded field/Save time was
741–866 ms on non-repair tasks; task 4 took 14.15 seconds including assistant
repair. These are local harness timings, not full model/tool round-trip latency,
not a matched performance comparison, and not a human-tempo claim.
There were zero helper-model calls; primary-model tokens/cost are unavailable.
The public API and handle bridge still use separately owned native connections.
Title polling is readiness evidence; only the independent exact submission
scorer establishes task success. Semantic text-effect feedback before Save,
general recovery, held-out workflow and matched model-cost evaluation remain.
