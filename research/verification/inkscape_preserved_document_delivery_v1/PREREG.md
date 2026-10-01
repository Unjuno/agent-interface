# Inkscape saved-document required/preserved-effect experiment

## Scientific question and chronology

Owner question: open Issue #34. Closed #2076's exact pure reducer (Git blob
3ccf652575837c5ab961e78b8e9d56c703f4187e) is reused; its historical experiment is
never run. The preceding chat-local exact-value and request-event studies remain
byte-preserved. #4007 is already publishing the first of those and is not duplicated.
This changes application/evidence boundary: actual Inkscape document actions,
saved SVG, independent geometry and raster evidence, rather than a custom SQLite
or Tk callback fixture. #4006's undo/notification experiment is separate.

GitHub writes are not exposed in this session. This is a LOCAL prospective
registration, not a public GitHub preregistration. Source hashes are recorded in
FREEZE.json before the first formal batch. Publication limitation is a run record,
not a new fleet-wide blocker or a reason to repeat a consumed experiment.

## H — falsifiable hypothesis

A requested target translation can be exact while another document object moves,
is deleted, changes color, or is duplicated. A target-only completion policy then
makes an unsupported complete-success claim. Binding a full saved-document view
and protected-object inventory/properties to the request allows the unchanged
#2076 reducer to distinguish complete, partial, failed and unknown outcomes.
Additionally, exact full-page pixels can be identical for a correct document and
one with a perfectly overlapping duplicate, so image equality is insufficient
for this explicit no-extra-object document contract. This is known information
loss characterized through an actual app, not a new general theorem or an
allegation of an Inkscape/runtime defect.

## T — finite, source-frozen experiment

Allocation: inkscape-preserved-document-34-20260922-01.
Three repetitions, eight scenarios per repetition, 24 new input/output documents.
Prospectively fixed three serial batches of eight; no formal retries, replacement,
pooling or parameter tuning. Each batch has an exclusive consumed marker and an
observed external runner exit; later batches require earlier exit-zero and raw hash.
Each application subprocess has an eight-second timeout; each batch has a
35-second supervisor timeout. Stop on incomplete/source/process evidence.

Fresh 320x180 unit-scale SVGs contain two opaque, axis-aligned, ungrouped rects,
IDs target and sentinel. Three repetitions vary initial positions deterministically.
Request: translate target +30 user units horizontally; preserve its color, every
other rect's box/color, and the exact original object-ID set. No stroke, external
CSS, complex transforms, text, clipping or unknown shape support is claimed.

Fixed scenarios: MOVE_TARGET, MOVE_BOTH, DELETE_SENTINEL, RECOLOR_SENTINEL,
DUPLICATE_SENTINEL, NO_EFFECT, MOVE_SENTINEL, PARTIAL_TARGET. Effects are performed
only by installed /usr/bin/inkscape actions and SVG export. They are intentional
controls; no frozen script edits an exported document. The CLI is application-
specific automation, NOT the public Agent Interface CLI or keyboard/mouse path.

Each case: independently query before.svg; invoke actual action/export; start
another Inkscape process to query after.svg; start another process to render its
full page to PNG. Thus 96 actual application processes in the formal denominator.
Retain argv, actual PID/exit, stdin-free invocation, stdout/stderr, original and
saved SVG, query values, PNG, monotonic brackets, contracts/decisions and hashes.
Fresh private HOME/profile per case; DISPLAY is absent. No host desktop, model,
provider, credentials, user documents, network experiment, installs or native input.

Three reporting views per actual document: full; collateral evidence explicitly
withheld; incorrect after-document digest. These 72 reports are NOT 72 independent
application trials. Identical documents are consumed by target-only and full
policies; full policy evaluates additional declared obligations. Raster diagnostic
compares decoded full RGBA of MOVE_TARGET and DUPLICATE_SENTINEL within each
repetition. PNG encoding equality is not required.

Construction is disjoint: discovery probe, eight-case source-01 without renders,
eight-case source-02 with renders; 15 final pure tests. Source-02 showed identical
pixels for the duplicate case before this freeze; this is explicitly a planned
replication of that construction observation, not a blind discovery. Added final
unsupported-global-CSS refusal is unit-tested and changes no supported fixture.

## D — frozen decisions

PASS_INKSCAPE_PRESERVED_DOCUMENT_SCOPED only if all 24 cases/72 views/96 real
application process exits reconcile; exact source and all original files verify;
MOVE_TARGET yields 3 complete positives; the four primary-correct collateral
conditions yield 12 partial outcomes; no-effect/wrong-target/partial-target yield
9 failures; all 48 withheld/digest views are UNKNOWN; target-only has exactly 12
false complete claims relative to the full contract; all three duplicate pairs
have identical decoded pixels but one additional rect; separate raw-only audit
has no errors and all 14 preregistered semantic corruption controls reject.

Target-only remains FAIL_REQUIRED_ONLY_COMPLETION_POLICY even when the hypothesis
passes. Any complete contradictory application result is scientific FAIL/HOLD,
not an excuse to change the gate. Missing artifacts/source/exits are STOP/HOLD.
Original reducer label PARTIAL_PRIMARY_RESTORED is retained in raw; the new adapter
maps it to PARTIAL_REQUIRED_EFFECT_ONLY. No restoration is claimed by that label.

## C — assumptions / competing interpretations

The command purposely affects the wrong selection in controls. It demonstrates
an insufficient completion policy, not an application malfunction. A weaker task
which permits changes to other objects could legitimately accept those outcomes.
Image equality cannot recover hidden document multiplicity. The new preservation
contract costs extra evidence/verification; no efficiency comparison is made.
The query and renderer use the same Inkscape implementation; a separate minidom/
Decimal/Pillow auditor and saved bytes cross-check them but do not provide an
independent application trust root. All artifacts are stable between reads.

## U — limits

One app/version, controlled native-CLI fixtures, finite cases; not OS-input or
model-in-loop integration, general SVG validation, authenticity, arbitrary race,
crash durability, complex styling, power loss, GUI focus/release, time/token
savings, production qualification or completion of #34/#57/#2789/ROADMAP.
The provided Linux execution container has no Docker/Podman CLI or image digest.
No Docker/OrbStack equivalence or attested network-none image is asserted.
Clock frequency and host contention are uncontrolled. Timings are diagnostic;
no calibrated combined uncertainty u_c or coverage factor k is available.

## Typed variables and units

| Symbol/field | Meaning | SI unit | Definition | Domain/assumptions | Type |
|---|---|---|---|---|---|
| primary | Requested target box matches | 1 | Current box compared with frozen translated box | true/false/unknown | Boolean or null |
| preserved | Protected state unchanged | 1 | ID set, target color, other boxes/colors compared | true/false/unknown | Boolean or null |
| binding | Exact document/request evidence valid | 1 | SHA-256, input contract and process receipt checks | true/false | Boolean |
| x,y,w,h | SVG position and size | no SI physical length measured | Unit-scale viewBox coordinates | finite decimals; nonnegative sizes | Scalar |
| translation_x | Requested horizontal displacement | same SVG user unit | 30 | frozen integer | Scalar |
| index,repetition | Case and block identity | 1 | 0..23 and 0..2 | exact integers, not booleans | Scalar integer |
| start_ns,end_ns | Process/verification clock brackets | s (stored ns) | CLOCK_MONOTONIC samples | same container; ordered | Integer scalar |

Unit check: document width/viewBox-width and height/viewBox-height are both 1,
so requested translation, XML geometry, native query geometry and rendered
coordinates share the declared 1:1 mapping. This is NOT a conversion from pixels
to measured physical meters. Timing comparisons never mix monotonic and UTC.

## Conditional correctness argument

Assume complete truthful snapshots from the restricted supported document and
correct request identity. If target and all protected properties match, the full
contract is satisfied and the reducer returns complete. If target matches but a
protected property differs, the contract is not satisfied and the reducer returns
partial. If target does not match while evidence is complete, it returns failure.
If required evidence/binding is missing or invalid, the adapter returns unknown.
These alternatives exhaust the Boolean/null inputs created by this adapter.
This argument does not prove the producer or parser is correct; actual exported
bytes, independent XML/query/raster checks and finite controls test that residual.

## Roadmap / integration decision

Intake/ownership -> predecessor read-only audit -> excluded app construction ->
local source/environment freeze -> three first-outcome batches -> independent
raw audit/corruption checks -> additive source/raw/report/patch -> permitted PR
publication/review/current-head CI -> main readback -> only dependency-safe own
branch cleanup. The concrete handoff is a constrained saved-document verification
candidate, not an unused generic validator or a promoted runtime replacement.
