# Writer cell-selection scope: real-application fallback transfer

**Scientific result: PASS_WRITER_CELL_SELECTION_SCOPE_SCOPED.**
**Publication: HOLD_GITHUB_WRITE_CAPABILITY_UNAVAILABLE.**

This report was written after the one retained allocation
`writer-cell-selection-w4m8-20260926-01`. All 24 fresh Writer/Xvfb cases completed.
No formal case was retried, replaced, pooled with construction, or tuned after
measurement. This is a real-application, application-specific caller experiment,
not a production runtime promotion, model evaluation, or completion of #2311.

## Question and lineage

Open #2311 asks whether a declared fallback actually preserves an operation's
obligation. Closed #1919 assumes such equivalence in its abstract snapshot
contract. The previous conversation-local `fallback_selection_s8r2` tested
selection extent in Tk. The present study changes the application and the
write-scope question: replace the entire text of **Writer table cell A1 only**
with `7`, preserving three other cells, the table structure, and outside text.
No earlier allocation or result was changed or rerun.

Current-main intake and the final MCP read both returned
`4c701cc51b06296268ad8d9ae3eff1dd6f2d379d`. README, active CURRENT_GOAL,
ROADMAP, recent open/closed Issues, recent open PRs, the first 100 branch names,
and targeted Writer/selection Issue/PR/branch searches were inspected.
No matching Writer cell-selection allocation was returned. This was bounded,
non-atomic reconnaissance; it cannot exclude private or unpushed work.

## H / T / D / C / U

| Item | Frozen question and retained scope |
|---|---|
| H | Ctrl+A has context-dependent write scope; post-selection range checking prevents collateral text changes, while a verified-empty-cell route can recover useful progress that refusal-only gives up. |
| T | Four states, three policies, two fresh repetitions: 24 actual Writer/Xvfb lifetimes. Exact source, schedule, auditor and gates were frozen in this conversation before any formal case. |
| D | Complete 24-case integrity, the exact 4/4/6 completion counts, candidate collateral zero, explicit refusals, neutral native endpoints, actual exits, and 12 effective corruption controls. |
| C | The candidate gets trusted current UNO selection/context evidence. This is extra information and work, not an equal-information or equal-cost contest. No concurrent writer occurs between the last check and input. |
| U | Arbitrary documents, protected/merged/nested cells, independent model choices, temporal races, full-runtime authority, broad reliability, latency/tokens and production adoption remain untested. |

## Observed results

Each policy has eight directed cases: NONEMPTY, EMPTY, MULTILINE and WRONG_CELL,
two independent fresh repetitions each. WRONG_CELL starts the Writer text cursor
in B1, while the task still names A1. Ordinary positives have the cursor in A1.

| Policy | Cases | Exact A1-only result | No task-text refusal | Wrong result | Protected-content changes | Native emissions |
|---|---:|---:|---:|---:|---:|---:|
| BLIND: Ctrl+A, then type | 8 | 4 | 0 | 4 | 4 | 48 |
| RANGE_GUARD: Ctrl+A, check full A1 range, then type or refuse | 8 | 4 | 4 | 0 | 0 | 40 |
| EMPTY_AWARE: check context, type directly in verified-empty A1; otherwise select/check | 8 | 6 | 2 | 0 | 0 | 28 |

The blind policy remains **FAIL_TARGET_SCOPE** in its four directed failures.
A hypothesis PASS does not convert those failures into successful actions.
Refusals are not completions. RANGE_GUARD changes selection before refusing;
its refusal is task-text-free, not a claim that no GUI state changed.

### Decisive empty-cell example

Initial cell values were A1 empty, B1=`keep-b`, A2=`keep-c`, B2=`keep-d`.
BLIND's Ctrl+A produced a real `SwXTextTableCursor` with range `A1:B2`.
After native typing, A1/B1/A2 were empty and B2 was `7`, in both repetitions.
The table structure and outside body remained, but the three protected cells
were changed. This is not merely a failure to edit A1.

RANGE_GUARD observed the table-selection type and sent no task text. EMPTY_AWARE
verified the collapsed selection belonged to empty A1 and inserted `7` without
Ctrl+A, preserving all protected content. This supplies two additional exact
completions relative to RANGE_GUARD in the same eight directed conditions.
It is not a population success-rate estimate.

For WRONG_CELL, BLIND replaced B1 with `7`. Both guarded policies refused task
text; EMPTY_AWARE did so before sending any selection or text keys. NONEMPTY
and MULTILINE replaced A1 only in both repetitions under every policy.

## Why this is a capability/fallback issue

The official Writer shortcut documentation describes Ctrl+A as selecting the
whole table when the current cell is empty, and the current cell's contents
otherwise. That known command contract is not a novel defect. The experiment
measures the actual composition with a narrower, target-only edit obligation.
A route label such as SELECT_ALL does not establish the selected domain.

The candidate checks current table/cell context, exact source text, selected
text-object identity, selection representation and endpoint equality. For a
nonempty A1, a full A1 range is required. For an empty A1, the same range checks
establish a collapsed A1 selection, so expansion is unnecessary. The complete
conditional argument and variable/unit table are retained in PLAN.md.

This does not make read/check/type atomic. A new writer or focus transition
after the last read could invalidate the condition. Existing Writer post-guard
and UNO-serialization research is not repeated, refuted, or repaired here.

## Actual implementation and isolation

Provided Linux 6.18.44 x86_64 execution container; CPython 3.13.5, system Python
3.13.5 with UNO, LibreOffice 25.2.3.2 520(Build:2), Python-Xlib 0.15, native
X11/XTEST, SAL_USE_VCLPLUGIN=gen. Each case used a fresh authenticated,
TCP-disabled private Xvfb at 1024x768 depth 24 and a fresh Writer profile.
The guest reports AMD EPYC 9V74; CPU frequency/load are uncontrolled. There is
no performance benchmark or Docker/OrbStack/image-attestation claim.

Exact unchanged backend blob `9cae101a219348077668c8fc086acf8e13154afe` is retained
in vendor/backend.py. The loader omits one unused core-manifest import; executed
backend methods are unchanged. This is NOT public CLI/MCP, core admission,
a full authority lease, or complete unified-runtime validation.

UNO uses a private named pipe. Before READY it creates the fixture and initial
cursor. After READY it accepts snapshots, evidence save and close only; it does
not assign task text or repair selection. All post-ready task-text changes are
from native XTEST keys. A common 150 ms settling interval precedes readback;
this is an operational wait, not a latency guarantee. ODT save is an explicit
UNO evidence-collection operation, not an exercised GUI Save workflow.

A pure subprocess receives only the allowlisted current selection/context
packet. It gets no condition name, protected-cell content, saved document,
expected score or future effect. Returned eligibility is non-authoritative;
there are no actual rich-model/provider calls. No host desktop, user documents,
clipboard, package installation or external-network experiment was used.

## Independent result scoring and validation

The separately implemented stdlib auditor parses each saved before/after ODT's
content.xml without loading UNO, Xlib, the policy or the runner. It reconciles
all four cell texts, 2x2 table structure, protected-cell XML and every non-table
body subtree with raw UNO receipts, native stages, policy messages, raw capture
bytes, source/spec identities and actual external/direct process exits.
It does not certify all formatting, automatic styles or package metadata.

- Frozen raw-only audit: **898 checks, 24 cases, errors=[]**.
- All **12** well-formed copied-evidence mutations were changed and rejected.
  The mutated row digest was repaired, so detection was not just a stale hash.
- **10** pure policy unit methods passed before freeze and again after formal.
- All **146** frozen files and **7** executable identities matched afterward.
- **38** native stages: 20 selection chords and 18 text operations, 116 emitted
  native events total. Every stage has a verified tracked release and independent
  neutral X-server keymap/button observations.
- **48** actual before/after captures and **48** before/after saved ODTs retained.
- All **24** case waits and **72** direct peer/office-launcher/Xvfb waits were
  observed successful. All **96** recorded identities were absent afterward.
  Private-group scans were empty before rescue and at final cleanup; formal
  timeout/rescue count was zero. These facts are not an arbitrary daemon or
  hardware-input safety guarantee.

The auditor's independence is implementation/process separation by the same
author, not independent human or external review. Finite mutation coverage is
not a proof of universal auditor soundness. Clock values are diagnostic,
same-host monotonic nanoseconds only; no calibrated combined uncertainty is
invented. Raw depth-24 capture storage is 32 bits per pixel, not physical area.

## Construction and first-outcome preservation

CONSTRUCTION.md and original files remain frozen. Direct soffice.bin launch
exited 81; its UNO peer failed to connect before native task input. A later
successful application launch was followed by a title-based lookup failure,
again before task input; forced cleanup and a stale fixture lock file are kept.
The lookup was repaired before freeze using the unique visible Writer class.
Two further probes exposed table selection and its native text effect.

Five complete supervised construction cases, using different text and `8`, were
excluded from formal. Their raw audit made 169 checks without error. The third,
refusal-only policy was added to the initial two-policy draft before freezing to
separate protection from recovered completion. PLAN_DRAFT.md is preserved.

A Chromium option was rejected before browser launch because a managed policy
blocked every URL. No policy was altered or bypassed. This is a local feasibility
record, not a scientific failure or a separate successor work order.

## Source freeze and publication chronology

Freeze SHA256:
`e16448502bec44efbcd64476f2c55e4a3b6862ab078b9a355e54f7d27652b67d`.
The plan and hash were linked in this conversation at formal 0/24. This is a
conversation-local prospective freeze, **not GitHub preregistration**.

The GitHub connection exposes read-only actions; directory discovery found no
alternate write tool, and gh is absent. No GitHub Issue, comment, new branch,
PR, commit, merge or deletion was performed in this continuation. The proposed
namespace and local branch name are not remote reservations. PENDING_ISSUE_2311.md
and PR_DRAFT.md are drafts, not posted records.

Historical #2245 remains incomplete, not rerun. Its branch still points to
`8b6f30564e2091ecb6820570fd488c95eae584df` and no open PR has that branch as base.
The unresolved publication and absent delete operation mean it was retained,
not called disposable. Prior s8r2 evidence was only used for exact source
retrieval; its original ZIP hash is retained in CARRY_FORWARD.json.

## Review without running science

Run `python -B verify.py` in the extracted study directory. It verifies the
complete distribution and original source freeze, then reruns only the frozen
raw-only auditor, mutation controls and pure unit tests. It launches no Writer,
X server, UNO peer, backend, case runner or formal allocation. The original
source/case paths are evidence, not a request to replay consumed cases.

The distribution includes all frozen files, all formal raw/ODT/receipt data and
postformal review material. Fresh Writer profiles and duplicated working.odt
files are excluded. Nine two-byte construction dconf stubs and one stale,
fixture-owned lock receipt are retained because they are in the original freeze;
they contain no user data or authentication cookie. No fonts are distributed.

## Integration decision

Retain the measured target-scope constraint and the candidate's limited useful
progress, pending real-path compatibility review. Do not install the caller as
a generic selection or authorization policy. Full #2311 needs model-facing and
broader application/workload evidence. No token, latency, cost, reliability,
production or repository-wide roadmap completion follows.

Primary references (accessed 2026-09-26; current docs are not the measured binary):
- Writer shortcut table: https://help.libreoffice.org/latest/en-US/text/swriter/04/01020000.html
- XTextRangeCompare: https://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1text_1_1XTextRangeCompare.html
- XTextTableCursor: https://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1text_1_1XTextTableCursor.html