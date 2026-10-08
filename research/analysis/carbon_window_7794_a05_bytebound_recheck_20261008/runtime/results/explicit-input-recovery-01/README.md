# Explicit same-session input recovery

Code: `c26f30a7b63766cc1aed1b0aa4b307ee3e4540c5`.
Portable SHA256:
`c44402dbce3454d701c978f3ea1d9cc345cff83c1463e0825c6b43e10018e78a`.

The preceding uncertain-press fix preserves release targets after a send/sync
failure. However, after unverified cleanup, all ordinary public dispatch remains
blocked, including a release-only program. Previously only closing the persistent
owner retried cleanup through the public MCP surface. This correct refusal rule
left no explicit same-owner recovery operation.

The new `interface_recover_input(current_binding_revision)` calls the existing
release/readback path only when that same persistent-X11 session is already open
and requires input recovery. It never reconnects or replays an application action.
Only verified empty release clears the motor block. Success advances the binding
revision and invalidates pending target reviews; old requests/programs refuse.
Failed readback keeps the block. Application effects remain unknown: observe and
review before choosing a new program. This is not a new lease or freshness source.
One-shot and guarded tool sets remain unchanged. The local X11 session also has
an explicit recovery method; its caller owns serialization.

## Retained real stdio MCP constructions

Both allocations use private Xvfb/Openbox, actual XTEST/keymap calls and an
explicit test wrapper that raises after the first processed press and omits the
first cleanup release. This forces a reproducible held-input recovery condition;
it does not measure the frequency of naturally occurring failures. No model,
GUI task policy or shared resource/GPU workload is involved.

Before (`x11-explicit-recovery-before-01`, previous portable runtime): the first
dispatch reported execution_failed and recovery_required=true; an independent
connection confirmed W down. A subsequent ordinary release-only program refused,
and W remained down. Explicit close then released it. This existing result is
preserved without relabeling it as a runtime-contract failure.

After (`x11-explicit-recovery-after-01`, exact new portable runtime): the same
forced failure and ordinary-program refusal occurred. The explicit recovery call
then verified empty release; independent readback confirmed W up before any later
dispatch or close. Binding revision advanced from 1 to 2. A repeated recovery
request and a full pulse program using revision 1 both refused. After a read-only
capture, a separately authored revision-2 pulse completed on the same session;
independent readback again confirmed up. Historical recovery retrieval returned
the original release without invoking another operation. Explicit close and SDK
context exit completed normally; owned display/manager processes were reaped.

These are programmatic input-boundary constructions. The capture is not claimed
as primary-model semantic review or evidence of a completed application task.
No elapsed-time, model-token, human-tempo or task-performance improvement follows.
The fault wrapper and launch arguments are retained alongside both runtime builds.

## Validation

270 protocol + 122 harness tests passed. New controls cover strict empty-readback
requirements, failed recovery retaining the block, unopened/stale requests not
releasing, revision invalidation, persistence failure before recovery, historical
reads not repeating it, and tool availability only on persistent public X11.
Existing serialization/cancellation, observation-preserves-recovery and target
review invariants remain covered. Recovery cannot guarantee release when the
display connection/server is inaccessible, and is not a hard-time watchdog.

Raw data, build identity, source, request/reply/cleanup records and tests are kept
in `raw.tar.gz`. Verify their hashes and scoped outcomes without executing them:

```sh
python3 -O runtime/results/explicit-input-recovery-01/verify.py
```
