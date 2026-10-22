# Standard-caller blocked-release Xvfb attempt — run 39228685920

## Provenance

- PR: [#9171](https://github.com/Unjuno/agent-interface/pull/9171)
- PR head: `3984c9341712c043ae45912ba2af3d332c16f555`
- GitHub merge-ref SHA recorded in report: `a636608dfe244182770be50ee7ff74712d317d51`
- Workflow: [Runtime X11 v1 Integration run 39228685920](https://github.com/Unjuno/agent-interface/actions/runs/39228685920)
- Job: `x11-integration`, private Xvfb step failed; evidence artifact upload succeeded
- Runner: Ubuntu x86_64, Python 3.12.15, Xvfb `2:21.1.12-1ubuntu1.8`
- Xvfb binary SHA-256: `6b27845931670c8c9b3ce7423696a452ce3cab1c7f316ce5f7ea7f1297fa2f84`
- Artifact ZIP SHA-256: `e66227f6c94eb01950d5b5326ae39867e7264ee76e23e9ff649ef4794cabb4e9`
- [Raw result](result.json), SHA-256: `21c54af48dd7f507e4850302966297c893c66a2a8e6b683f6d6a7b537948acc1`
- [Observed image](observation.png), SHA-256: `751e00d5f926a15128a45baec1b2310aabee740b363119bd79dd224986d81f01`

## Result and diagnosis

The report confirms that the corrected owner marker directory was
`/tmp/mcp-xvfb-blocked-release-p_do8x0a/mcp`, matching the directory passed to
`create_server`. The standard caller returned `pending`, then the test timed
out waiting for `xvfb-delayed-request-queued.json`. It recorded a process and
window generation, a visible target image, an `a` input obligation, and an
owner process retired after a supervision timeout. The independent release
readback, delayed-request marker, blocked-sync receipt, application effect,
late-request horizon, and terminal result were not captured. The terminal
report says `EOFError()`, cleanup `UNKNOWN`, `release_confirmed=false`, task
success null, and replay disabled.

The test source identifies the remaining instrumentation defect: the wrapper
signature used `time` as the XTEST timestamp parameter, shadowing the imported
`time` module. After the original and delayed XTEST calls were queued and
flushed, the wrapper attempted `time.monotonic_ns()` before writing the marker.
The JSON does not contain this Python exception or prove exactly which XTEST
call completed, so keep that diagnosis explicitly source-derived. A new source
revision imports `monotonic_ns` under a non-shadowed name; this run remains a
test-harness failure, not a bounded-release result.
