# Cancellation keycode identity candidate repair T0

## H / T / D / C / U

**H:** Adding the resolved X keycode to the V12 owner's admission receipt is
sufficient to join cancellation intervals to admitted physical keys under the
same owner mapping. Multiple key symbols that resolve to one keycode must stay
grouped as one physical interval rather than being represented as separate
key-up events.

**T:** Apply the single frozen byte-level source mutation in `repair_probe.py`
to the exact archived V12 candidate from A01, then rerun the injective and
alias fake-Xlib arms. `repair_audit.py` independently validates the source
blob, mutation digest, and saved dispositions without re-executing the owner.

**D:** PASS for this source-mutation construction if the injective arm's
admission keycodes match its two release keycodes and the alias arm records
both admissions as keycode 77 while retaining one keycode-77 cancellation
interval. Any mismatch is a FAIL for this candidate repair.

**C:** A keycode is a physical-key identity only within the X server/keymap
epoch that resolved the symbol. This experiment does not handle a keymap change
during a lease; a live design must either hold the map stable or record and
validate its epoch. It also does not establish whether duplicate symbol
admissions are allowed by the higher-level action contract.

**U:** One-line mutation under synthetic Xlib only. No source was changed on
main; no real X server, GUI, physical input, game, model, scorer, recovery,
formal allocation, or performance measurement was used. This result suggests
a minimal measurement-field candidate but does not prove production readiness
or justify a live run by itself.

## Result

The construction passed. With the injective mapping, admission identities
`[87, 65]` match release intervals `[87, 65]`. With both symbols mapped to 77,
admissions carry `[77, 77]` and the owner correctly emits one physical
keycode-77 interval. The A01 limitation is therefore repaired at the
physical-key grouping level for this candidate mutation. A01 remains preserved
as the unmodified baseline result.

The first patch-fixture attempt did not match because the frozen source uses
CRLF; the exact byte pattern was corrected before executing the candidate
mutation. No candidate source was executed on that failed fixture attempt.

## Reproduction

```powershell
python research/doom/map01_cancel_keycode_identity_59_t0_a01_20261004/repair_probe.py
python research/doom/map01_cancel_keycode_identity_59_t0_a01_20261004/repair_audit.py
```
