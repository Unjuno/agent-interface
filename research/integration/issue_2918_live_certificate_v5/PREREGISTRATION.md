# Issue #2918 live certificate transfer — allocation 05

## H/T/D/C/U

**H.** A state-conditioned minimum certificate derived from fresh pixel
evidence at the public X11 observation boundary can safely suppress forwarding
on changes outside the prior certificate mask; masked changes and uncertain,
stale, partial, missing, contradictory, replaced, ambiguous or intent-epoch
mismatched cases fail open. Allocations 01–03 and audit-only allocation 04
remain preserved as STOP/HOLD; none are repeated or rewritten.

**T.** Run a new one-shot 12-case allocation using the exact frozen #1904
compiler/candidate and the same preregistered state/decision schedule.
Allocation 04 identified an overlapping-window defect in allocation 03. In
this new fixture, the second same-role window for ambiguity is placed at
`(700,20)`, while the primary target is at `(20,20)`; a separate construction
smoke confirmed a fresh public-API capture still samples the primary window's
colored pixel after the second window is mapped. Capture the complete
intent-mismatch observation before exit. The independent auditor checks
matching target IDs, non-overlap, all receipt and epoch lineage, PNG hashes
and pixels, stale timing, independent minimum masks and terminal decisions.

**D.** `PASS_LIVE_MANIPULATE_CERTIFICATE_SCOPED` only if all 12 rows and 11
public API captures survive; ambiguous target produces two non-overlapping
matching windows and zero API calls; all case bytes, XIDs, bindings, epochs,
capture/decision/generation times and hashes reconcile; both unmasked
transitions safely suppress using the prior minimum mask while phase-union and
global controls forward; the masked transition forwards and changes the
independent terminal result; all seven uncertainty controls YIELD; the
read-only-input independent auditor exits zero and writes its result on the
separate report mount; and no input/authority is present. Otherwise preserve
FAIL/HOLD/STOP. One runner invocation and one audit invocation; no retry or
post-start source changes.

**C.** OrbStack Docker 29.4.0, pinned local linux/arm64 image, `--network
none`, read-only root/source, private Xvfb, explicit `PYTHONPATH=/repo`,
allocation-specific fresh raw output, read-only audit input and separate
writable report directory. No model/provider/network, GUI input, real
application, task effect or production claim.

**U.** Whether complete fresh live pixels and caller-visible binding/epoch
lineage safely support minimum-certificate reuse in this fixture, including
when a second matching target exists elsewhere on the display. No real-app
effect or end-to-end cost claim is tested.

## Frozen source and environment

Previous results are immutable under allocations 01–03 and audit-only 04.
Candidate/compiler bytes are identical to allocation 01. The one-time source
hashes, exact commands, container image, mount layout and `PYTHONPATH` are
listed in `SOURCE_FREEZE.json` before any formal observation.
