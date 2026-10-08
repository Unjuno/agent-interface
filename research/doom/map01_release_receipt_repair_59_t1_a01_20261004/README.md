# V11 applied-release receipt repair comparison T1 A01

## H / T / D / C / U

**H:** V11's ordinary key-up and button-up receipts can claim X release plus
sync even when V10's owner has no corresponding held input and issues neither
release request nor sync. A minimal producer repair should add an opt-in V10 release-receipt call path that returns the resolved keycode for key operations and explicit `release_applied`, request-issued, and sync-completed evidence from the owner thread. Existing V10 `call("up")` and `call("button_up")` return values should remain unchanged. For no-ops, it must retain the
RPC caller interval but leave the release-transition interval absent.

**T:** Run the exact V10/V11 source blobs pinned in `FREEZE.json` under the
existing controlled FakeDisplay. Apply the generated `CANDIDATE.patch` to the
checked-out V10/V11 sources and require byte-normalized equality with the
generated candidate before execution. Exercise injective W/A keycodes, aliased
W/A keycodes, repeated key-up, and button-up with no held button. Count actual
release requests and sync calls; compare those deltas with candidate receipt
claims. Run the checked-out V11 owner contracts and typed backend provenance
contracts under the same FakeDisplay stubs. The typed backend's inherited
session superclass is stubbed because its import closure requires VizDoom on
this Windows host; the actual typed backend class and release forwarding method
are exercised by those tests. Also run its actual `raw` method with V11 and feed
the emitted rows to the reconciliation oracle, with admissions at program steps
0/1 and release calls at steps 2/3.

**D:** The hypothesis reproduces if the baseline reports successful release
and sync on alias and repeated-up no-ops with zero added calls. The candidate
passes its scoped criterion if applied receipts carry matching identity and
true request/sync fields, while no-op key/button receipts carry false fields,
retain only a caller interval, and add no release request or sync.

**C:** Aliased symbols are synthetic and this draft implementation is not
production-qualified. The additive V10 operation/method and V11 caller path
require compatibility review in every selected backend. The evidence does not
show whether a live keymap aliases W/A.

**U:** FakeDisplay only. No real X server, physical input, game, model, GUI,
scorer, recovery, performance measurement, or live allocation. A returned
release request plus XSync still does not prove hardware state or application
consumption. Failure behavior when XTest or XSync raises needs separate
integration testing.

## Result

The source-pinned baseline reproduced false-success receipts for the second
aliased key-up, repeated key-up, and unheld button-up. Each added zero release
requests and zero sync calls. The candidate preserved injective and first
aliased release identity and reported each applied request/sync. Checked-out
V10 ordinary key-up and button-up return values remained `None`; admission
receipts gained the resolved keycode. Six V11 owner tests and six typed backend contract tests pass against the checked-out sources. An integrated V10/V11/typed-backend run joins admissions at steps 0/1 to applied/no-op release calls at steps 2/3 and groups them into one keycode-77 interval in this failure-free fixture. For the
second aliased key-up, repeated key-up, and unheld button-up, it reported
`release_applied=false`, both operation flags false, and
`release_transition_interval_ns=null`, while retaining `call_interval_ns`.
Saved counts match those claims. See `RESULT.json` and `audit.py`.

Follow-up failure-boundary construction A02 found an important interpretation
limit: when XSync raises after the server has applied KeyRelease, a later retry
can return `release_applied=true` although fake key state was already up before
that retry. Thus this receipt proves request and XSync completion inside the
call bracket; it does not independently prove that a key-state edge occurred
inside that bracket. See
`../map01_release_receipt_failure_boundary_59_t1_a02_20261004/`.

## Reproduction

```powershell
python research/doom/map01_release_receipt_repair_59_t1_a01_20261004/probe.py
python research/doom/map01_release_receipt_repair_59_t1_a01_20261004/audit.py
python research/doom/map01_release_receipt_repair_59_t1_a01_20261004/run_v11_unit_fake_xlib.py
```
