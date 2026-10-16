# Follow-up repair: retain per-key up records on aggregate-query failure

This package is a repair successor to the fake-display record-loss reproduction already reported in [PR #7815](https://github.com/Unjuno/agent-interface/pull/7815). It does not repeat that experiment as the scientific result; it tests a narrow owner/bridge repair against the exact #7805 V13 owner/V2 bridge source pair.

## H/T/D/C/U

**H:** When owner cleanup confirms a per-key key-up but later aggregate pointer/keymap verification raises, the current candidate loses its local measurement list and leaves owner and bridge hold ledgers stale. Persisting a partial release record and retiring each confirmed owner hold should preserve the per-key receipt while preventing an aggregate-neutrality claim; the owner must fail closed.

**T:** Inject a failure on keymap query 5: two admission samples, two per-key release samples, then aggregate verification. Exercise cleanup inside `Backend.execute()` so its existing finally/drain path runs.

**D:** Preserve the exception; emit exactly one contextual `CONFIRMED_PHYSICAL_UP`; require fake physical state, bridge-held keys, and owner-owned keys to be empty; require the active owner lease to be cleared. The partial record must say `verified=false` and use unknown aggregate key/button lists (`null`).

**C:** The unmodified owner blob is `82d3881dd4064f58e847420bb336a70cd84ee307`; bridge blob `ee1220cdc3d93d96aa1051c072ca7dceeb59c35d`. These are the exact source blobs from #7805 head `32686927ce6b07a035beb4c0297171a1f951c6c6`, also used by #7815. Supporting source blob IDs and the cached offline container pin are in `SOURCE_LOCK.json`. The package preserves source, repair diff, probe, focused/compatibility runners, raw RED/GREEN logs, and an independent raw/source audit.

**U:** This is synthetic fake-display evidence. It does not establish real X11 behavior, game input effects, useful feedback, recovery efficacy, live threat response, latency, or MAP01 outcome. No GUI, game, OS input, or live allocation was used. A per-key sampling failure before a confirmed up is outside this probe. The host's WSLc reported that memory was limited without swap because swap cgroup limits are unavailable.

## Result

Baseline RED: no release row, `F8` remained in both software ledgers, and the fake physical state was neutral. Repair GREEN: the aggregate exception propagated; one confirmed-up receipt was emitted; both ledgers became empty; the owner had no active lease; aggregate verification remained explicitly false. The focused candidate suite passed 8/8 and owner compatibility passed 10/10 against the repaired copy. `audit.py` verifies those claims from the frozen raw logs and source blob identities.

This package is an isolated follow-up candidate, not a change to #7805, #7815, or `main`. Current-main detached composition is not included.

## Replay

Unzip this package into a directory mounted read-only at `/src`. Run the repair probe, focused suite, and owner compatibility runner with the pinned image and command limits in `SOURCE_LOCK.json`. The runners use the included frozen source fixture and fake display only.
