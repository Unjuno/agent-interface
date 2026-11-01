# Cancellation after the guarded owner exits

This fixed-order WSLc before/after experiment used an actual spawned guarded
owner and private Xvfb. The owner sent `a` to an independent target; a test hook
paused the owner after the press, and the harness terminated the owner before
calling `cancel_guarded`. The X server stayed alive.

| Observation | Previous candidate | Changed candidate |
| --- | --- | --- |
| Key state after cancellation | `a` down | `a` down |
| Cancellation status | `not_active` | `cancel_unconfirmed` |
| Cleanup state / replay | omitted | `UNKNOWN` / disallowed |
| Published owner obligation | omitted | `a` keycode from retired child shared state |
| Release attempted by cancellation | No | No |

In both trials the target observed the `a` press. The harness explicitly
released the still-held key and then a fresh guarded task succeeded. The
changed result preserves review-required, task success unknown, and possible
late request; `input_dispatched=false` describes the cancellation signal, not
the original action. The change prevents an unexpected owner exit from being
reported as an ordinary inactive cancellation. It intentionally does **not**
claim or attempt automatic release in this path: without exclusive display
custody, a late release could affect a different client's hold. Existing
recorded cleanup evidence is preserved if present. A single liveness check also
avoids an intervening exit falling back to `not_active` on a second check.

The new regression test failed against the prior candidate and the final
candidate passed 63 offline supervisor/owned-process tests in WSLc. Trial
conditions, hashes, target events, result receipts and test outputs are in the
included manifests and `raw.zip`. An intermediate regression whose mounted
source changed during execution is excluded from the passing claim. The
private X authority files are excluded; both generated cookie records were
scanned in raw and hexadecimal form against packaged material. WSLc reported
that the memory limit did not enforce swap.

This result does not solve automatic recovery after unexpected process death,
establish a hard deadline, or prove general input ownership. Safe automatic
release still requires exclusive/fenced display lifecycle integration.
