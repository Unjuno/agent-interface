# Standard-caller blocked-release Xvfb attempt — run 39228136905

## Provenance

- PR: [#9171](https://github.com/Unjuno/agent-interface/pull/9171)
- PR head: `7d7360f22cdd33bb15e23aa094e7384d359a9a56`
- GitHub merge-ref SHA recorded in report: `e0b8ae9308b8225d06419bf1bb2dae26cece5e12`
- Workflow: [Runtime X11 v1 Integration run 39228136905](https://github.com/Unjuno/agent-interface/actions/runs/39228136905)
- Job: `x11-integration`, private Xvfb step failed; evidence artifact upload succeeded
- Runner: Ubuntu x86_64, Python 3.12.15, Xvfb `2:21.1.12-1ubuntu1.8`
- Xvfb binary SHA-256: `6b27845931670c8c9b3ce7423696a452ce3cab1c7f316ce5f7ea7f1297fa2f84`
- Artifact ZIP SHA-256: `ad44107966480075fe05a4214db75d8b4ade6d89646a3f805f68eacc6070455b`
- [Raw result](result.json), SHA-256: `32468b9e2f149d9832d77c6d8a4848ce54af46c45caabce7ffb8104564985315`
- [Observed image](observation.png), SHA-256: `751e00d5f926a15128a45baec1b2310aabee740b363119bd79dd224986d81f01`

## Result and limits

The private-Xvfb observation returned both process and window generation hashes;
the guarded alias was minted and the MCP input call returned `pending`. The test
then failed waiting for `xvfb-delayed-request-queued.json`. Source inspection
shows a marker-directory mismatch: `create_server` is given `root / 'mcp'` as
its output directory, `OwnedGuardedSessionOwner` passes that path to
`_guarded_owner_factory`, and the factory writes markers beneath the received
directory. The test waited beneath the temporary parent `root` instead of
`root / 'mcp'`.

The report records the terminal error `EOFError()`, owner process retirement
after a supervision timeout, an `a` input obligation, `release_confirmed=false`,
cleanup `UNKNOWN`, task success null, and replay disabled. Its PID-qualified
disconnect row says `disconnected`, with expected owner PID 2771 and observed
PID 2778 on the same resource base. However, the report has no delayed-request
marker, blocked-sync receipt, pre-cancel application effect, independent
release readback, or late-request horizon. Because the test observed the wrong
directory, these records do not prove whether the injected event was queued or
whether the owner entered the intended blocked sync. The final keymap check
occurred only during cleanup and cannot establish release of an independently
observed held key.

This is a test-observability failure with partial caller/cleanup telemetry, not
a bounded-release pass. The raw JSON and PNG are copied unchanged from the run
artifact. Align marker observation with the owner factory's actual directory
and run at a fresh source revision before evaluating the release boundary.
