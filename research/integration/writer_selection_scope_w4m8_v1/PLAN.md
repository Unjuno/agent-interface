# Writer cell-selection scope: prospective first-outcome allocation

Allocation: `writer-cell-selection-w4m8-20260926-01`.
Issue lineage: open #2311, closed analytical #1919, previous chat-local
`fallback_selection_s8r2` Tk experiment. No old allocation is repeated.
Intake main: `4c701cc51b06296268ad8d9ae3eff1dd6f2d379d`.
Proposed additive path: `research/integration/writer_selection_scope_w4m8_v1/`.
Proposed branch: `research/writer-cell-scope-20260926-w4m8`.
These names are local coordination labels, NOT remote reservations.

## Scope and question

Transfer selection-obligation checking from a cooperative Tk fixture to actual
LibreOffice Writer. Replace all text in a designated A1 cell by `7`, retaining
three other cells, a two-by-two table, and all body content outside the table.
The support contract concerns text and structure, not all formatting or arbitrary
documents. Calling Ctrl+A is not itself an assertion about what is selected.

The official Writer shortcut reference documents context-sensitive Ctrl+A:
a nonempty active cell selects its text; an empty cell selects the table.
This is known behavior, not a newly discovered application defect. The empirical
question is how this behavior composes with a target-only replacement obligation
and a bounded no-model caller.

## H — falsifiable hypothesis

BLIND uses Ctrl+A then text without inspecting selection scope. RANGE_GUARD uses
the same one Ctrl+A but types only with a complete A1 text-range receipt.
EMPTY_AWARE checks current A1 context before selection; it types directly into a
verified empty A1, otherwise uses one Ctrl+A and the same full-range check.

Expected: BLIND loses protected text in empty-A1 and wrong-cell cases. RANGE_GUARD
prevents the text changes but refuses empty-A1 progress. EMPTY_AWARE completes
empty-A1 and ordinary positives, while refusing wrong-cell input. No action
selector is allowed to claim task success; effects are scored independently.

## T — exact finite execution

Supplied Linux x86_64 execution container, CPython 3.13.5, system Python 3.13.5
with UNO, LibreOffice 25.2.3.2, Python-Xlib 0.15, Xvfb, native XTEST. Docker/gh
are absent; no Docker/OrbStack or image-attested equivalence. Exact versions,
binary digests and uncontrolled clock/CPU conditions are in ENVIRONMENT.json.

The original Chromium transfer option was rejected before browser launch because
a managed URLBlocklist forbids every URL. No browser policy, credentials or
access control was modified. This is a local feasibility record, not a new Issue.

Four states: NONEMPTY A1=`north`; EMPTY A1=empty; MULTILINE A1=`north\nsouth`;
WRONG_CELL A1=`north` but current Writer text cursor in B1. Neighbors initially
B1=`keep-b`, A2=`keep-c`, B2=`keep-d`. The body outside the table is the exact
ODT XML subtree created by the source (`outside-before`, a line break, and
`outside-after` in one paragraph). The table precedes that paragraph; these
literal labels do not assert a before/after geometric position.

Three policies, two fresh repetitions per state: 24 cases. Repetition zero orders
BLIND/RANGE_GUARD/EMPTY_AWARE, repetition one reverses this order. Exact opaque
scopes and per-case source inputs are fixed in SCHEDULE.json and specs/.
Each case creates a new authenticated TCP-disabled Xvfb, fresh Writer profile,
real office process and UNO peer. No model/provider, experimental external
network, user desktop, user files, package installation, clipboard or old run.

UNO creates a document and initial cursor before readiness, then accepts only
read-only snapshot, evidence save, and close. No post-ready text assignment,
selection repair, invoke, dispatch, or simulated key event occurs in the peer.
The candidate never sees the condition, expected final state, other-cell values,
or saved ODT. Its packet is an exact allowlist built from current UNO selection.
Scope IDs are opaque and carry no condition words. A separate policy subprocess
has a minimal environment and no app access. The runner selects actions from its
typed output; it never uses final-scoring data to decide an action.

The source-exact existing X11Backend methods emit all selection/text keys.
Whole backend blob: `9cae101a219348077668c8fc086acf8e13154afe`.
The loader omits only the unused core-contract manifest import. Methods are not
changed; manifest/core admission/lease/public CLI/MCP are NOT exercised.

Every native stage is one chord or one text operation followed by release_all.
A common 150 ms settle precedes readback; it is not a latency gate or guarantee.
If the chosen readiness/effect ordering fails, retain failure rather than retry.
Native full keymap and button-mask observations are independent of backend
tracked-key release claims. X-server logical state is not physical HID telemetry.

Retain full before/after ODTs, raw pixels/capture brackets, source/specs, actual
UNO request/response bytes, selected TextRanges/TableCursor type and cell range,
object-scope comparisons, exact native programs/emission/release reports, all
policy stdin/stdout, actual subprocess and outer waits/exits, and process-group
residue checks. Runtime-generated private authentication files are deleted and
not included in evidence. Fresh profile caches are excluded from publication.

## D — fixed gates

PASS_WRITER_CELL_SELECTION_SCOPE_SCOPED only if all 24 cases and the frozen
source/schedule/evidence/process controls reconcile:

| Per policy, eight cases | Correct A1-only result | Input-free task-text refusal | Wrong/collateral result |
|---|---:|---:|---:|
| BLIND | 4 | 0 | 4 |
| RANGE_GUARD | 4 | 4 | 0 |
| EMPTY_AWARE | 6 | 2 | 0 |

EMPTY/BLIND must expose real table selection A1:B2 and after-state A1/B1/A2 empty,
B2=`7`; WRONG_CELL/BLIND replaces B1 by `7`, leaving A1 unchanged. Positive
NONEMPTY/MULTILINE states replace A1 only. RANGE_GUARD refuses EMPTY and
WRONG_CELL after selection but before task text. EMPTY_AWARE emits exactly one
text stage without Ctrl+A for EMPTY, and emits no keys for WRONG_CELL. No
refusal is counted as task completion. Selection changes remain visible and are
not described as zero state effect.

All admitted native programs must release keys/buttons, with neutral independent
endpoint readbacks. All three direct child waits and the external case wait
must be exit zero, no timeout, no private-group residue before rescue, no socket
or authentication residue. Missing source/raw/process evidence is STOP/HOLD.
Complete contrary effects or candidate collateral are FAIL at the relevant gate.
Preserve negative comparator status FAIL_TARGET_SCOPE even when the research
hypothesis passes. No scientific benefit, timing or reliability probabilities
are inferred from this finite matrix.

A separate retained-data auditor parses ODT content.xml using only Python stdlib;
it never imports UNO/Xlib/controller/policy. It checks the table dimensions,
every cell text, protected-cell XML subtrees, and all non-table body subtrees.
Automatic style definitions, metadata and whole-package byte identity are not
an invariant. It also reconciles every policy packet, stage, wire, capture,
actual exit and denominator. Twelve predeclared well-formed evidence mutations
must reject, with modified row digests repaired so semantic checks do real work.
A separate implementation/process by the same author is not external human review.

## C — alternatives and assumptions

A stock UI context changes Ctrl+A semantics; this is not a timing race or backend
bug allegation. The target is explicitly supplied by fixture setup, not found by
a semantic model. UNO reports are cooperative current application evidence, not
authentication. No writer changes text/focus between the last check and input.
An empty cell with a collapsed caret must belong to A1, not just have empty
selected text. The object identity plus cell/table context must be checked.
Extra observation and process work has real cost; no equal-cost, latency or
model-boundary comparison is made. Refusal-only is not task completion.

## U — what is not established

No model-facing selection, true two-domain model acceptance, general fallback
coverage, arbitrary tables/documents/custom bindings, merged/protected/nested
cells, concurrent user edits, input-lease correctness, application rollback,
GUI Save semantics, natural failure prevalence, speed, token saving, monetary
saving, cross-platform or production promotion. Evidence save is a UNO call
for independent post-action scoring, not a demonstrated keyboard-save workflow.
No automatic retry or repair of any failed native text operation is authorized.

## Explicit decision variables and units

| Field/symbol | Meaning | SI unit | Definition/domain | Type |
|---|---|---|---|---|
| scope | observation session identity | 1 | nonempty opaque string, must equal expected_scope | categorical scalar |
| seq, minimum_seq | current and minimum observation order | 1 | strictly positive integers, booleans excluded | integer scalar |
| target_text, expected_text | current and authored source A1 text | not physical | exact Unicode strings, must agree before input | string |
| active_cell, active_table | current recipient context | 1 | exact A1 and TargetTable for candidate input | categorical scalar |
| kind, count | UNO selection representation and range count | 1 | TextRanges with exactly one range; null count for TableCursor | categorical/integer |
| same_text | selected text object belongs to A1 | 1 | strict boolean true, not integer 1 | boolean |
| start_cmp, end_cmp | range boundaries relative to A1 endpoints | 1 | strict integers; both zero denotes equal endpoints | integer scalar |
| selected_text | text within current selected range | not physical | exact string equality with target_text for replacement | string |
| phase, policy | bounded step and policy arm | 1 | prepare/selected; fixed policy enum | categorical scalar |
| t | monotonic observation/call time | s | stored as integer nanoseconds; one same-host clock domain | integer encoding of scalar time |
| w, h | capture dimensions | 1 | positive discrete pixel counts, not metres | integer scalars |

Unit check: sequence IDs and range comparisons are dimensionless and never
compared to timestamps. Only same-clock monotonic timestamps are ordered. Raw
TrueColor capture storage is four bytes per pixel at depth 24; width*height*4
is a storage byte count, not physical area. No calibrated combined uncertainty
or coverage factor is manufactured for diagnostic clocks.

## Conditional justification, without a logical gap

1. The required write domain is the complete text object of A1; all other
   cell/body subtrees are protected by the task contract.
2. For a nonempty cell, a single selected TextRange has the required domain only
   when its text object is A1 and both endpoints equal A1's endpoints. Matching
   selected bytes alone is insufficient because another cell can have the same
   value. The candidate therefore requires object, context, endpoints and value.
3. Under the explicit standard-replacement and no-intervening-writer assumptions,
   typing into that verified range replaces exactly A1's old text. No old prefix
   or suffix remains inside A1, and the write range does not include other cells.
4. If A1 is empty and the selection is the collapsed A1 range, typing at that
   range inserts the requested text in A1. A selection-expansion chord is not
   needed and can change the write domain; the candidate does not send it.
5. If target context or selected domain cannot be established, no task text is
   sent. That is a refusal, not proof that the task has been completed.
6. These implications do not establish that Writer actually implements the
   assumptions on this build. The fixed live cases and saved-document scorer
   test that empirical remainder. A different actual effect must remain FAIL.

## Stop and evidence delivery

One invocation per case, in frozen order. Source mismatch or failed/unfinished
case stops the allocation; no following cases, denominator filling, rerun,
replacement, pooling or post-result tuning. Each external supervisor bounds its
case to 30 s plus bounded owned-group cleanup, below the outer tool limit.
Retries of a readonly auditor do not create new scientific rows and must use a
fresh output; they never alter original evidence.

Source/gates are frozen and linked in this conversation before case zero because
GitHub MCP exposes only reads and gh is absent. This is conversation-local
preregistration, NOT a remote public preregistration. No access-control bypass
or alternative credentials are used. Results, exact byte manifest and a reviewable
additive patch are delivered locally; GitHub publication remains a separate HOLD.

Roadmap: intake/ownership check -> excluded setup and five complete construction
cases -> source/auditor/control tests -> exact freeze -> 24 first cases -> raw
ODT/native audit and 12 controls -> scoped report/patch -> permitted future PR,
applicable checks/main readback -> only evidence/dependency-safe owned cleanup.
The global ROADMAP and #2311 remain open regardless of this finite outcome.

Primary references:
- https://help.libreoffice.org/latest/en-US/text/swriter/04/01020000.html
- https://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1text_1_1XTextRangeCompare.html
- https://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1text_1_1XTextTableCursor.html