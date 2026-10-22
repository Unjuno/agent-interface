# MCP worker interruption evidence and explicit recovery

Base main `1b1c0064e4acc32f4aa451218130db3ac33a4e55`.
Ordinary Fake X construction and regression; no native/display/game/model,
WSL/container, or historical formal allocation executed.

## Problem and repair

The worker used a finally block to mark an interrupted call finished, but a
KeyboardInterrupt/SystemExit could leave no saved report. The preceding backend
repair still attempted release and quarantined input, yet its in-memory snapshot
could not be retrieved through MCP. A previous successful report could also
hide a later presentation interruption if receipt persistence failed.

The worker now records a separate `interruption.json` before rethrowing a
non-Exception stop. It does not convert the stop to ordinary success, resume a
program, issue recovery or overwrite any existing `report.json`. Metadata marks
the interrupted call, publication success or persistence failure. A new backend
interruption snapshot is copied only when its object differs from the snapshot
at that call's entry: a prior recovered call's snapshot is not attached to a
pre-dispatch or presentation stop.

`interface_results` selects the acknowledged interruption receipt. If that
receipt could not be saved, it reports unavailable instead of falling back to a
completed backend report. Retrieval issues no input. The receipt preserves the
attempted call's session/quarantine and task-effect unknown state; it does not
claim physical release from a finished worker or a written file.

## Executed composition

Six new methods pass normal and optimized Python:

- Custom worker stop after an actual fake CTRL press: same-call prefix/cleanup
  snapshot, full/brief lookup, no replay.
- Pre-dispatch stop with a previous snapshot: no stale execution attribution.
- Before/after-report interruption, with OSError or SystemExit during receipt
  persistence: original stop wins and lookup remains unavailable.
- Presentation stop after a completed backend report: original report bytes are
  retained and lookup describes the interruption separately.
- Owned Python child processes, actual KeyboardInterrupt/SystemExit: original
  stop reaches the outer process harness after the receipt is written; fake
  state is neutral. Full normal-mode child outputs and artifact trees are in
  `probes/`; the complete suite also exercises both interpreter modes.
- Actual bounded-response MCP calls: return pending while the worker is gated,
  reject concurrent close, then retrieve the fatal worker's receipt and perform
  explicitly chosen release-only recovery. Review/fresh grounding remains
  required and the suffix is never pressed. These use a continuing in-process
  MCP server; they do not restart a terminated server.

The unchanged pinned original MCP module fails nine assertions/zero errors in
five of these methods, normal/-O. The owned-child method is excluded from that
base-source control because its child imports checkout source. An intermediate
repair's report fallback failed two additional directed assertions before it
was fixed. Original RED/fallback failures and final logs are retained in `raw/`.

[RESULT.json](RESULT.json) records final suite counts/skips;
[SOURCE_PINS.json](SOURCE_PINS.json) joins tested Git blobs and actual checkout
bytes. [CONDITIONS.json](CONDITIONS.json) records commands, test source, scope and
post-execution evidence construction. Raw nanosecond stamps are diagnostic
backend clocks, not physical timing measurements or independent incident trials.

## Remaining gates

The existing JSON writer flushes/fsyncs its temporary file and renames it; this
work does not prove power-loss durability, bounded filesystem writes or restart
discovery of a previous server's in-memory call registry. Directly awaited
KeyboardInterrupt/SystemExit may terminate its event loop/server; the owned
probe catches that stop to inspect the saved artifact. The continuing pending
path and the direct fatal path are distinct results.

Native transport liveness/physical release deadlines, process death, device and
cross-backend custody, independent application effects, bounded semantic recovery
and matched economics remain open in #17/#59/#57. This is evidence recovery and
input-neutralization composition, not a completed live task or permission to
replay an interrupted action.
