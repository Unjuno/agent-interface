# GUI compensation: preserved state and current Undo history

Issue #4043. This is retained research evidence, not a runtime change. Closed #2076/#3936 are preserved; #16/#34/#2197/#2789 and the repository roadmap are not closed by these results. Parallel #4006 concerns external callback effects and #4038 concerns keyboard-modifier ABA, neither of which is rerun here.

## Findings and distinct allocations

**Earlier scope rung: PASS_UNDO_SCOPE_BOUNDARY_SCOPED**, allocation `text-undo-scope-20260922-01`, 24 fresh Tk processes in three immutable eight-case batches. With protected `p` followed by agent edit `x`, ordinary Undo removed both in 3/3 cases; an application-provided edit separator preserved `p` in 3/3 matched cases. Final dispositions were 9 COMPENSATED_SCOPED, 3 FAIL_COMPENSATION_COLLATERAL and 12 ABORTED_PARTIAL_NO_UNDO. All 24 endpoints were neutral. Refusals and no-Undo controls are not successful compensations.

**Prospective history rung: PASS_UNDO_HISTORY_BOUNDARY_SCOPED**, allocation `text-undo-history-4043-20260922-01`, 12 new Tk processes in two immutable six-case batches. Current text can return to the receipt's text while Undo history changes. In the directed ABA condition, native `y` insertion followed by separately grouped BackSpace restores `base:px`; ordinary Undo then restores `y` instead of removing the agent's `x`.

Each cell below contains two fresh sessions. Both policies see the same declared history, but run in separate fresh applications.

| History | Receipt/current revision | TEXT_MATCH | REVISION_BOUND |
|---|---|---|---|
| CLEAN | 2 / 2 | Undo; `base:p`, 2/2 | Undo; `base:p`, 2/2 |
| CHANGED | 2 / 3 | refuse; `base:pxy`, 2/2 | refuse; `base:pxy`, 2/2 |
| CONTENT_ABA | 2 / 4 | **wrong Undo**; `base:pxy`, 2/2 | refuse; `base:px`, 2/2 |

History-rung dispositions: 4 COMPENSATED_SCOPED, 2 FAIL_WRONG_COMPENSATION, 6 UNRESOLVED_NO_UNDO. All 12 final server key/button states and cleanup queries are neutral. The boundary-hypothesis PASS does not erase comparator failures or convert unresolved refusals into compensation success. Do not pool these 12 cases with the different earlier 24-case allocation.

## H / T / D / C / U

**H.** Matching current text and target/session does not identify the intended Undo operation after intervening edits. A receipt additionally bound to the observed edit revision can refuse this declared changed-history case. TEXT_MATCH is an explicitly unsafe fixture comparator, not an allegation about production code.

**T.** Protected native `p`, application-provided F12 separator, native `x`, then one of three frozen histories; compare TEXT_MATCH with REVISION_BOUND, two repetitions, fixed six-case order per batch. The ordinary Tk Text Undo binding is unchanged. F12 is this application's explicit `edit_separator` operation, not a generic Tk/system cancellation shortcut. After readiness, controller IPC exposes snapshots and close only, never direct insertion or Undo. Exact original fixture.py is reused. Native XTEST keys drive effects; app-owned journals and final.txt, raw pipes, focus ancestry, independent server keymap/button queries and actual process exits are retained.

**D.** All 12 case identities, exact texts, revisions, native key sequences, received app events, file hashes, process exits and neutral states must reconcile with frozen expectations. Both CLEAN controls compensate, both CHANGED controls refuse; CONTENT_ABA must expose wrong TEXT_MATCH Undo and revision-bound refusal. Nine rehashed copied-evidence mutations must reject. Complete disagreements remain FAIL/HOLD; source/process/missing-evidence uncertainty remains STOP/HOLD. No retries, replacements or post-freeze source/threshold edits occurred.

**C.** Cooperative Tk revision metadata covers the observed content changes, not every possible hidden Undo-stack mutation. No writer intervenes after final validation. This is neither an authenticated history certificate nor an atomic check-and-use solution. Different applications, edit grouping rules and external side effects require separate evidence. The general fact that Undo operates on grouped edits is documented by Tk; the contribution is the retained interface/compensation counterexample and guard boundary, not discovery of Undo or ABA itself.

**U.** One controlled ASCII/Tk fixture, two cases per history/policy; no population failure probability, latency/speed/tokens, rich-model decisions, crash safety, cross-platform or production qualification is established. Monotonic timestamps are diagnostics, not calibrated performance measurements; no combined measurement uncertainty or coverage factor is assigned.

## Environment and chronology

Provided Linux x86_64 execution container, CPython 3.13.5, Tcl/Tk 8.6.16, Python-Xlib 0.15, private authenticated TCP-disabled Xvfb 640x240x24. The history environment records 151 source/binary/library hashes. No Docker/OrbStack image-attestation claim, installs, network experiment, provider/model request, user desktop/documents/clipboard, shared runtime change or other worker session.

Intake main: `e4c2e58122aa138e421048d8e86ec18259143b9e`. Main/README/CURRENT_GOAL/ROADMAP, recent open/closed Issues, open PRs, two branch pages and targeted Undo/ABA searches were inspected through GitHub MCP. Unpushed work is unknown; only the two issue-owned additive namespaces are used.

The earlier 24-case allocation was already performed in the previous conversation with local freeze `2026-09-21T20:11:01.685680Z` on intake `81a004527e5124e54fb1f4da5785fc0c5640ef50`. Issue #4043 records it retrospectively, NOT as a new or retrospectively preregistered GitHub run. Its original startup/focus construction STOPs and publication-unavailable notes remain unchanged. Only raw-only audits were rerun: all three old audit outputs are byte-identical to the originals.

The new six-case construction passed and is excluded. Nine pure gate checks and nine construction mutations passed. Before new formal execution, FREEZE.json was committed at `644594443476c1e1cfceb976fae3cb8da400190f`, Git blob `17667a1642b1e36121ef3b1233a9c6c5f03e7315`, and read back exactly. Issue comment 5768288097 records formal 0/12 and the commands. Two once-only bounded batch invocations then returned actual exit 0; comment 5768298761 preserves the first outcome. Separate audit implementation/process: 6/6 plus 6/6, zero errors; nine rehashed semantic mutations reject. This is not independent human review.

## Exact evidence and verification without GUI execution

CAPSULE.json describes eleven binary parts of one lossless tar.xz: 315 regular files / 2,162,210 original bytes. It contains `previous/` (202 old files, byte unchanged), `history/` (108 new files including complete readable frozen source, raw evidence and audits), and `continuation/` (five previous re-audit records). No PNG re-encoding, PRNG reconstruction or numeric approximation is used.

Archive: 88,192 bytes, SHA-256 `7c06ca65796e4e81cb35c04bb8c96f5a05c5d531de346331075ff02bd376f043`.
New freeze SHA-256: `46b8ca3fa3249874573011df54560d8c71ddb3aa73bef2968aba43755131c981`.
New RESULT.json SHA-256: `e0aecbe45293772f9577ad3a06bc1ea27a14b4b35ff638cb0344f387d987ba16`.
Old source tar.xz SHA-256: `271bd65930e750610567af29f54850c63fe30363914afbf5d31164af18828a90`.

From this directory, using standard-library Python only and a fresh absolute destination:

```bash
python unpack.py /tmp/undo-4043-review-01
python /tmp/undo-4043-review-01/history/audit.py /tmp/undo-4043-review-01/history/formal-0 --batch 0 --output /tmp/undo-4043-review-01/review-0.json
python /tmp/undo-4043-review-01/history/audit.py /tmp/undo-4043-review-01/history/formal-1 --batch 1 --output /tmp/undo-4043-review-01/review-1.json
python /tmp/undo-4043-review-01/history/controls.py /tmp/undo-4043-review-01/history/formal-0 --batch 0 --output /tmp/undo-4043-review-01/review-controls.json
```

These commands restore/audit bytes; they do not import Tk/Xlib or execute an allocation. **Do not run history/execute.py or previous formal launchers against consumed allocations.** Complete protocols and source are retained for review, not an invitation to repeat until PASS.

Publication validation restored all 315 files byte-for-byte, including every old member. Both new raw audit outputs match their original hashes exactly; all nine semantic mutations still reject. Six unpacker controls reject relative/existing output, missing/changed/reordered parts and a changed part with its manifest rehashed. See PUBLICATION_VALIDATION.json. Evidence digests and decoding verify integrity, not truth by themselves; the independent raw audit checks the application/effect relationships.

## Integration decision and remaining roadmap

Use three separate obligations: current compensation scope/history evidence before input; unconditional physical release once active; independent verification of required restoration AND preserved state after compensation. Current text equality and input neutrality satisfy neither all scope nor all effect obligations. A refusal remains unresolved and may need richer recovery; the study does not authorize automatic Undo or certify arbitrary revision producers.

Connections: HCI edit grouping and user-visible Undo scope; transaction compensation with protected invariants; distributed versioned receipts and ABA invalidation. These are transfer ideas, not measured cross-domain benefits.

The scoped scientific roadmap is complete through first-result audit. PR/main delivery and safe own-branch cleanup are recorded in Issue #4043 separately. This file does not claim a merge before it happens. The full runtime/model/task-cost roadmap remains open.

Primary mechanism reference: Tcl/Tk Text manual, Undo section, https://www.tcl-lang.org/man/tcl8.6/TkCmd/text.htm (the retrieved manual is 8.6.18; measured implementation is 8.6.16).
