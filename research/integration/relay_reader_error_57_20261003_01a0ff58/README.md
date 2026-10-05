# Child stdout Readline failure: explicit uncertainty, no replay

At main3e93df3, a real child stdout stream error is forwarded by Readline to
an Interface with no error listener. Test-first native Windows/Node24.19.0
produces three unhandled-error process exits1: before a request, while one
already parsed inert request is pending, and after a response settled. The
fragmented Japanese/emoji/normal-EOF control passes. Node's documented input
error forwarding supports the mechanism:
[official Readline error event](https://nodejs.org/api/readline.html#event-error).
This package's actual version-specific evidence is the retained Node24 run.

The production correction is one line: reader.on('error', fail). It reuses
the existing blocked state/pending rejection. The same promise becomes delivery
uncertain and forbids replay; an already returned result remains returned.
No extra request is recorded. Explicit transport close reconciles the inert
child exit. This does not claim physical release or a real MCP action's result.
The fixture's COMMITTED marker means its Node child parsed an inert JSON line,
not that a backend/SDK accepted or performed an operation.

Four new regressions in the existing workflow-selected test_relay_client.mjs
retain their first-red definitions unchanged. Source commit6841eec follows
ordinary tests; its runtime/test blobs equal those tested bytes. The full
relay-client/host checks pass33/33 and necessary existing caller/exchange/stdio
checks pass56/56. No full CI/platform/runtime claim. The source/readback/actual
commands/exits/UTC/log hashes accompany each check. Node24.19.0 Windows is
measured; Node22/26, macOS/Linux, actual CLI reader-loss cleanup, spontaneous
OS fault rates and GUI/model/task/latency/resource effects are unexecuted.

First green32/33 retains its sparse timing-helper import failure. Repairing the
test worktree's source inventory restores that existing Python helper; its
actual interpreter is3.13.14, separate from the3.12.14 capture process. No global
dependency/configuration was installed or changed. The first capture wrapper's
cp932 console print error occurred after complete Node raw/exit receipt capture;
original tool output retains that diagnostic, with no separate wrapper stderr
file falsely claimed. Ordinary setup repair did not relabel either first result.

The first publication check caught a JSON-escaped home prefix inside a failed
Node assertion log. The entire original 52-file projection is preserved privately
in publication-v1-original, manifest31e4a36b72288b0ba621ece6ccdbf9176890a5bafb703a554f92a4133f9d5d1c; it was never committed or published. A second publication recipe replaces
plain and JSON-escaped home prefixes before readback; original Node streams and
source/test definitions are unchanged. The initial validation script and tool
diagnostic remain preserved; no separate captured validator stderr is claimed.

Public paths use an explicit user-home-prefix projection; text/log line endings
are unchanged. JSON receipts are recursively projected/reencoded. PUBLICATION
maps original/private/public hashes and preserves private originals. Source
runtime/test/probe text has no user path and remains byte-exact. Archived
scripts have .txt extensions; the package has no automatic runnable tests,
imports or workflow changes. Old research sources and allocations stay exact.

This is distinct from#6919's command-input Interface handler, f520's#6919
Windows control review and b04b's public SDK overlap/backpressure check. Their
sources and frozen studies were not rerun or modified. Own#6879 fe42/v4 remains
unchanged. Content committee, actual-current-base/tree/nonauthor apply record,
effective GitHub requirements and one expected-old forward application remain
separate. No main write or shared input/Engine/GPU/apply lock.
