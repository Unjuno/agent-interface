# X11 recovery custody across serialized session wrappers

Base main `a392ff468abfe940634df8ef20e7c1aadc32e2a6`.
Ordinary Fake X construction, repair and regression. No native display/input,
game, model, WSL/container or historical formal allocation was run.

## Counterexample and repair

An X11 session quarantined itself after failed release, but a second session
around the same backend started with `recovery_required=False`. Both a
preconstructed sibling and a newly constructed replacement could press a
different key while the original key remained held in Fake X. A failed release
with an empty ledger was also forgotten. Checking only held keys cannot retain
the missing evidence.

Recovery-required state now belongs to the backend object. Session construction
uses that existing state rather than resetting it. Every newly required recovery
advances its epoch; each wrapper remembers which epoch it has acknowledged.
Verified explicit release-only recovery clears the backend requirement and
acknowledges the recovering wrapper. A wrapper predating the failure still needs
its own explicit recovery before dispatch, even after a sibling has recovered.
A fresh wrapper attached after the failure can observe verified recovery without
reviving an earlier alias context.

That distinction is necessary: a directed complete-module control removing only
the epoch test allows an old guarded alias to send input after sibling recovery.
The final guarded composition refuses that alias without any new emission.
Recovery through the guarded bridge then advances its binding, clears history
and requires review/fresh grounding. No operation is replayed.

Direct backend cleanup is not acknowledgement of a wrapper's context. Assigning
`recovery_required=False` cannot clear pending/stale state; use verified explicit
recovery. Failed or interrupted recovery keeps the shared obligation. A failed
new recovery after previous neutralization creates a new quarantine epoch.
The wrapper-local acknowledgement does not serialize calls: the existing
caller-serialization requirement still applies.

## Evidence

- Six backend methods exercise actual public dispatch, admission, whole-program
  preflight, execute, key-state, release and readback with the existing memory-only
  X fixture. They cover old/new wrappers, held and empty ledgers, direct cleanup,
  per-wrapper explicit recovery, failed/interrupted recovery, false-reset refusal
  and healthy replacement. Original failed release reports are retained in raw
  JSON stdout rather than rewritten as a successful later outcome.
- One supported Python bridge method exercises observe/mint/input, uncertain
  readback, sibling recovery, refusal of the old alias and the bridge's own
  explicit recovery. Only X/platform setup is fake at this layer.
- Final seven methods pass normal and optimized Python. Complete pinned original
  session source fails seven assertions/zero errors in the six backend methods.
  The no-epoch complete-module mutation fails one guarded method with a retained
  actual fake input trace. These controls pass no scientific/native gate.
- [RESULT.json](RESULT.json) records final affected suite counts/skips;
  [SOURCE_PINS.json](SOURCE_PINS.json) distinguishes tested Git blobs from checkout
  bytes. All first RED/repair/control-construction failures and final streams are
  retained in `raw/`, with conditions in [CONDITIONS.json](CONDITIONS.json).

The first state prototype re-marked a stale wrapper's successful readback as a
new failure and advanced the epoch again. Its one assertion failure is retained;
the repair marks custody only for failed readback. The first isolated control
runner hit a package-import cycle before tests; its four normal/-O control
streams remain, followed by the corrected runner's actual assertion failures.
These are ordinary construction repairs, not hidden scientific retries.

## Remaining gates

This is backend-object state in one Python process with trusted, serialized
callers. It is not a lock, durable authority, native input ownership or protection
against deliberate private-state mutation. A different backend/process does not
inherit this custody; related [MAP01 distinct-backend evidence](../../doom/map01_cross_backend_custody_20261016/README.md)
remains a separate unresolved path. No display-name registry or automatic
reconnect was introduced.

Native send/readback liveness, physical release bounds, device/read-access and
competing-client semantics, independent task effects/bounded semantic recovery
and matched economics remain open in #17/#59/#57. Verified fake neutralization
and a usable replacement session do not establish task completion.
