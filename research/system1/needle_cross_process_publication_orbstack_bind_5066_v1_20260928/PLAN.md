# Issue #5073 — OrbStack bind-mount publication probe

This is an additive, platform-specific successor to #5066. It preserves both
predecessors and makes no claim about Windows/Docker Desktop equivalence.

## H / T / D / C / U

The exact H/T/D/C/U and decision outcomes are frozen in `FREEZE.json` and
restate Issue #5073. Scope is one macOS host, one OrbStack context, Linux/arm64,
one pinned local Python image, one bind mount and one synthetic package. There
is no model, network, GUI, dispatch, or authority grant.

## Corrected concurrency gate

Eight persistent reader processes (four per arm) receive commands through
independent queues. In each of seven atomic phases, all four readers open and
retain the current ACTIVE descriptor before exactly one measured `os.replace`.
After replacement returns, each reader reads the held descriptor and then
opens the path afresh. The auditor checks `fd_open < replace_start <
replace_return < fd_read_end`, the exact old bytes through the retained handle,
and exact candidate bytes through the fresh path handle. This matches the
append-only validity clarification on #5073 and closes the serialized
pre/post-read defect in #5066.

The unsafe arm has seven truncate/prefix/write/completion phases. In each,
the writer pauses at a barrier after truncate and a strict prefix; each reader
opens and retains the observed partial bytes before the writer completes. The
readers then verify exact complete candidate bytes. All 56 phase-reader rows
retain raw bytes in base64 so the independent auditor can reconstruct hashes,
JSON and package digests without importing the runner.

## Formal boundary

Construction checks may run locally and do not invoke Docker or create formal
outputs. After source and freeze are committed/pushed, invoke one formal
container and one separate raw-only auditor container. Each gets source/input
read-only, output-only writable bind, network none, pull-never, read-only root,
bounded resources, dropped capabilities, and no-new-privileges. Any formal
invocation or output creation consumes the sole allocation; preserve failure
and do not retry.

## Integration

Retain raw outputs, execution receipts, hashes, and audit output under this
additive directory. Run local CI, record the formal outcome on #5073, and
integrate only via reviewed PR.
