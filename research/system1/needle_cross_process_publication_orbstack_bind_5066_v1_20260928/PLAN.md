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
independent queues. Each row records PID and monotonic read interval. In the
atomic arm, each of seven replacements is repeated in an open publication
window while the four readers each perform one synchronized observation batch
(32 snapshots). The audit requires every reader's read interval to overlap the
union of actual `os.replace` syscall intervals in every phase. A further read
from each reader is requested only after each replacement returns (28 post
rows). This corrects the serial-before/after schedule in #5066.

The unsafe arm has the corresponding seven synchronized read batches. At the
partial-write phase, the writer pauses at a barrier after truncate/partial
write while all four readers each take 32 snapshots; incomplete bytes must be
observed. The remaining phases use equivalent windows, changing only the
publication strategy.

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
