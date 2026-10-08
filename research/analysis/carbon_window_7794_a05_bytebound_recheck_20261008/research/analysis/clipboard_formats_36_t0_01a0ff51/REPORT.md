# #36 T0: format metadata does not establish saved paste effect

**Method result: PASS_METHOD_SCOPED.** One frozen candidate and one separate
raw-only auditor ran on 2026-10-03, 01:38:22–01:38:23 UTC; both container/client
exit codes were zero. Twelve saved Qt fixtures, eleven `paste()` calls,
48 diagnostic judgments, zero audit disagreements and ten specific-reason
mutation rejections. No candidate/auditor retry occurred.

**Disposition:** retain per-format dependency checking and exact saved-effect
verification as sufficient *for this fixture*. Do not require extra MIME-request
visibility here: the effect-only alternative detected every seeded wrong effect
and accepted one valid effect that the strict request/effect judgment held.
No runtime adoption, general clipboard safety or full #36 completion is claimed.

## What the executed test distinguishes

Qt QTextEdit and QPlainTextEdit actually pasted process-local QMimeData into
new documents. A declared plain-preference subclass and an HTML bold-stripping
subclass supplied adversarial target policies. Each outcome was saved as text
and Qt-generated HTML. The separate auditor used Python's HTMLParser to recover
saved text/style and reconciled it with the candidate's Qt document measurement.
It imported neither the candidate, gates nor Qt. Tests were development-known;
formal and construction rows were not pooled.

The four columns below are diagnostic judgments of the same outcome, not four
controllers or four separately executed live allocations. ELIGIBLE only means
the metadata dependency passed; it does not mean the effect was correct.
All deliberate diagnostic pastes ran irrespective of those judgments. A
post-paste check detects an already-observed effect and cannot prevent or undo it.

| Case | Observed saved effect | Summary digest | Format manifest | Manifest + request/effect | Manifest + effect only |
|---|---|---|---|---|---|
| C01 rich control | Alex, bold | ELIGIBLE | ELIGIBLE | VERIFIED_CORRECT | VERIFIED_CORRECT |
| C02 plain control | Alex, plain | ELIGIBLE | ELIGIBLE | VERIFIED_CORRECT | VERIFIED_CORRECT |
| C03 same plain, changed HTML | Eve, bold | ELIGIBLE | REJECT_DEPENDENCY | REJECT_DEPENDENCY | REJECT_DEPENDENCY |
| C04 same HTML, changed plain | Eve, plain | REJECT_DEPENDENCY | REJECT_DEPENDENCY | REJECT_DEPENDENCY | REJECT_DEPENDENCY |
| C05 target prefers plain | Alex, bold lost | ELIGIBLE | ELIGIBLE | WRONG_FORMAT | VERIFIED_WRONG |
| C06 target strips bold after HTML request | Alex, bold lost | ELIGIBLE | ELIGIBLE | VERIFIED_WRONG | VERIFIED_WRONG |
| C07 request visibility absent | Alex, bold | ELIGIBLE | ELIGIBLE | HOLD_FORMAT | VERIFIED_CORRECT |
| C08 external fixture owner/generation | Eve, bold | REJECT_DEPENDENCY | REJECT_DEPENDENCY | REJECT_DEPENDENCY | REJECT_DEPENDENCY |
| C09 no-paste control | empty | ELIGIBLE | ELIGIBLE | NO_EFFECT | NO_EFFECT |
| C10 synthetic token control | expected synthetic text, bold | ELIGIBLE | ELIGIBLE | VERIFIED_CORRECT | VERIFIED_CORRECT |
| C11 task accepts plain or rich | Alex, plain | ELIGIBLE | ELIGIBLE | VERIFIED_CORRECT | VERIFIED_CORRECT |
| C12 unavailable clipboard data | empty | HOLD_RESOURCE | HOLD_RESOURCE | HOLD_RESOURCE | HOLD_RESOURCE |

Among the five planted wrong-content/style cases (C03/C04/C05/C06/C08), summary
metadata left three eligible and the complete manifest left two eligible.
Both post-effect routes refused or detected all five. Of the five valid-effect
controls (C01/C02/C07/C10/C11), the strict request/effect judgment verified four
and held C07; effect-only verified all five. These are exact finite-case counts,
not population error rates. No statistical uncertainty or confidence interval
is inferred from this authored conformance matrix.

C06 directly challenges treating a requested format as proof of correct markup.
C07 challenges making format visibility mandatory when an exact saved-state
oracle is already available. Data retrieval was recorded at QMimeData's virtual
getter, with fixture consistency checks. It is **not independently established
as exclusive representation consumption**; no chosen-format receipt is claimed.

## Frozen provenance and evidence

- Protocol: [PREREGISTRATION.md](PREREGISTRATION.md).
- Source commit: `9cc86468601c2b68e7b9bbb595f55b5bf47d92b4`, based on inspected
  main `f1416985d4ff9ce5bbf9f0f4be1be3d0ee669549`.
- Prospective source SHA-256/image/limits/output identity: [FREEZE.json](formal/01/FREEZE.json).
- Raw and saved documents: [candidate/raw.json](formal/01/candidate/raw.json).
- Separate oracle reconstruction and ten mutation controls: [audit.json](formal/01/audit/audit.json).
- Exact create/start commands, client/container exits and start/end observations:
  [RUN_RECEIPT.json](formal/01/RUN_RECEIPT.json); pre/post source hashes and
  container inspections are beside it.
- [SHA256SUMS.txt](SHA256SUMS.txt) checks retained files. The launcher's source
  was fixed in the recorded creation/invocation command before running; its
  file hash was first recorded afterward, and is not in the initial FREEZE.json.
  This timing distinction is preserved rather than backdating the freeze.

The final image is
`sha256:9e9b1a232f08b8c437834f8a40a5b39ca4be9c66b953833170930c70fdc66d89`,
Linux arm64, Python 3.12.3, Qt 5.15.13, PyQt 5.15.10. Host: MacBookPro18,2,
ten logical CPUs, 64 GiB RAM, macOS 27.0.1. Guest kernel and Docker versions are retained.
One private Engine in `research-clipboard-36-01a0ff51-docker` ran the two
experimental containers sequentially, with network none, read-only root/source,
private output, 0.25 CPU/256 MiB/64 pids and private /tmp. Construction read
the corresponding guest cgroup settings; no host-pressure enforcement test was
performed. Other host workloads were not controlled, and no comparative latency
is reported. `elapsed_ns` is a diagnostic monotonic clock counter, not a benefit
measurement. No model was invoked, so model settings/tokens are inapplicable.

## Preserved construction outcomes

The optional isolated guest's first Docker build stopped before Qt acquisition
on an OCI BPF/cgroup restriction. This matches the upstream
[OrbStack isolated-machine Docker issue](https://github.com/orbstack/orbstack/issues/2429).
It was stopped without deleting evidence. The final ordinary dedicated guest
has standard macOS integration; it is not described as a host security sandbox.
No shared Engine or another worker machine was changed.

Construction01's original raw, sources and audit FAIL remain in `construction/01`:
the auditor predicted no MIME request for empty clipboard data, but Qt queried
text/plain before inserting nothing. Construction02 uses the corrected recorder
prediction and explicitly HOLDs the empty resource; its saved-state audit passes.
The test-first eight-failure baseline, the later empty-resource regression failure,
and both construction records are retained. Construction did not consume a
formal allocation, and its rows do not augment the formal counts.

## H / T / D / C / U and remaining boundary

The frozen H/T/D/C/U remain in the protocol unchanged. Its discrimination gate
passed. The stronger simple comparator limits the conclusion: full effect
verification, rather than mandatory format visibility, was sufficient here.
The extra visibility requirement is deferred for this fixture.

Only one item, two UTF-8 representations, uniform style, authored policies and
a known saved-state oracle were exercised. This does not test native clipboard
ownership/change detection, user focus, expiry, manager races, handoff, retry,
clock uncertainty, keyboard/pointer delivery, physical release or irreversible
application actions. QClipboard offscreen is process-local; Qt paste was real
toolkit behavior, not an OS cross-application input experiment. No browser,
Calc/terminal, user data, microphone, GPU or model was used. The planner metadata
view contained no synthetic token bytes, but real privacy safety is unproven;
digests of predictable values can leak information. #36 remains open.

The representation model is established prior art in the
[W3C clipboard specification](https://www.w3.org/TR/2026/WD-clipboard-apis-20260624/).
Qt's [rich-text insertion](https://doc.qt.io/archives/qt-5.15/qtextedit.html#insertFromMimeData)
and [plain-text insertion](https://doc.qt.io/archives/qt-5.15/qplaintextedit.html#insertFromMimeData)
are existing behavior, not a new Agent Interface mechanism. No shipped Qt
binary/image is published by this evidence package.

Local verification passed ten tests and the sparse-aware analysis index. Source/document diff checks passed. The complete diff check found three trailing spaces emitted in the immutable Docker version output (blank GitCommit fields); that raw file is preserved byte-for-byte and excluded from the source whitespace check. No remote CI was required by observed branch protection/rulesets; optional push/pull_request CI is skipped.

## Additive integrity correction — retained raw only

After the formal run, review of #6860's JSON-scalar issue prompted an additional
read-only probe here. The original v1 auditor rejects a boolean in observed
generation, but its planner_metadata dictionary equality accepted generation
1 replaced by True or 1.0 in the delivered metadata copy. These two original
acceptances are recorded in posthoc_v2/audit.json, not hidden or retroactively
added to the formal gate. The original formal packet, auditor, freeze, source
hashes, ten controls and first PASS_METHOD_SCOPED outcome remain unchanged.
The original PASS applies to those predeclared controls; v1 is known to have
this additional metadata-type blind spot.

Additive audit_v2.py uses a type-sensitive canonical JSON comparison for the
nested planner metadata while retaining v1's separate saved-state reconstruction.
Two regression subtests failed before the fix. A single supplemental ordinary
raw-only audit returned PASS_POSTHOC_AUDIT_SCOPED, accepted the unchanged original
packet, retained all ten specific original rejections and rejected both new
scalar corruptions for C01:planner_scalar_type. Twelve local test methods pass.
No candidate/container/formal allocation was rerun; this posthoc audit has its
own prospective source/raw provenance and receipt. Run it with
`python -B audit_v2.py --oracle oracle.json --raw formal/01/candidate/raw.json --output /new/path/audit.json`.
Use v2 for later read-only adjudication; preserve the original v1 result and
limits. The scientific format/effect table and comparator disposition did not
change. Content reviews target a new digest and committee epoch; old votes are
not copied to the corrected delivery.
