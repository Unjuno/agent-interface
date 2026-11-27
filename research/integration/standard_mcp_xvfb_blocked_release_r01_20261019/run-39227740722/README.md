# Standard-caller blocked-release Xvfb attempt — run 39227740722

## Provenance

- PR: [#9171](https://github.com/Unjuno/agent-interface/pull/9171)
- PR head: `a0f69e5157190ed5097b249be7e10f5d5da82845`
- GitHub merge-ref SHA recorded in report: `84e222b68fa2c76b8ce604cd1546263f6ec5b66a`
- Workflow: [Runtime X11 v1 Integration run 39227740722](https://github.com/Unjuno/agent-interface/actions/runs/39227740722)
- Job: `x11-integration`, private Xvfb step failed; evidence artifact upload succeeded
- Runner: Ubuntu x86_64, Python 3.12.15, Xvfb `2:21.1.12-1ubuntu1.8`
- Xvfb binary SHA-256: `6b27845931670c8c9b3ce7423696a452ce3cab1c7f316ce5f7ea7f1297fa2f84`
- Artifact ZIP SHA-256: `389b434426779024cbb3352a95d74e63059c7ecf70823462a1acf377e852416b`
- [Raw result](result.json), SHA-256: `4534eba02a25a9c47ec5f2397b36115cad07c8a0e59e7e1483937d3eb2e493ef`
- [Observed image](observation.png), SHA-256: `751e00d5f926a15128a45baec1b2310aabee740b363119bd79dd224986d81f01`

## Result

The test observed the private Xvfb window with 64-hex process and window
generation values, captured the checkerboard target patch, minted its guarded
alias, and received `pending` from the standard MCP input call. It then timed
out waiting for `xvfb-delayed-request-queued.json`.

The retained terminal report identifies the cause: the test's monkeypatched
`fake_input` wrapper did not accept the `root=` keyword used by
`Xlib.ext.xtest.fake_input`. It raised `TypeError` before invoking the original
function, so neither the immediate `a` press nor delayed `b` press reached
XTEST. The owner ledger had recorded `a` before backend dispatch; the test
therefore entered cleanup with an obligation but no observed application
effect. Its cleanup attempt also encountered the wrapper `TypeError`; a final
parent keymap check read both keys up, but with no press sent this says nothing
about releasing held input.

`input_before_cancel`, cancellation, independent release readback, late-request
horizon, terminal result, and synthetic application effect are null. Cleanup is
`UNKNOWN`, task success is null, and replay remains disabled. This is a second
test-harness failure, not a bounded-release or recovery result. The JSON and
PNG are copied unchanged from the downloaded run artifact; later runs must use
separate paths.
