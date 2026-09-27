# CLI review diagnostic fidelity — #4350 / r4k6

## Decision

**PASS_REVIEW_COMPILATION_FIDELITY** from one publicly source-frozen180-process
engineering matrix. Existing production behavior needed no change. Add8 permanent
regressions and saved-data verification, not a new compiler or validator.

Base: b669264a65d1474481e511676eacfc06bf82d775.
Public freeze:2969d9cb3db9ffde5b0addde754f80306a3475a3.
Source/input readback and prospective gate: Issue4350 comment5826784763.
First result: Issue4350 comment5826801947.
No evaluation reruns, row replacement/exclusion, or post-result scientific tuning.

## Why this boundary

The standalone validator from closed#4343 is already on main, so the prior p3j8
unified-archive alternative is not duplicated. Parent#3850 concerns usable failure
diagnostics. #4342 owns historical m9v2 GUI delivery; this work uses24 exact retained
responses as input and never reruns those GUI cases. Six additional inputs are
explicit copied controls, not historical observations. The original ZIP digest is
in INPUTS.json. All962 prior files were read-only revalidated before selection.

## Result and denominators

30 inputs x2 routes(file/stdin) x3 modes(plain/compact/report_refs) produced180
fresh CLI review processes. These are180 presentations, not180 GUI trials or tasks.
Historical execution statuses presented: completed48, execution_failed48, refused84.
Review-process exits:174 exit0 and6 missing-image exit2. A review exit0 never
converts an earlier execution failure/refusal into task success.

- Raw-only fixed auditor:5123 checks, errors=[].
- Eight effective copied-output mutations:8/8 rejected, baseline first verified.
- Permanent unit methods:8/8. Separate construction:18 processes,524 checks,8/8
  output mutations; none is pooled into the180-record denominator.
- Receipt schema:150 plain receipt-view-v1,30 reversible report-reference views.
- Exact source digest and full parsed original report are preserved in every case.
- All48 frozen file identities match before/after. All raw CLI exits are retained;
  outer launcher exit0 is stored independently. New GUI/native/model calls:0.

For mixed compilation, expanded failure index13 maps to source index4(0 based).
Explicitly expanded programs have no compilation field and retain index13 without
inventing another source mapping. Inconsistent/boolean maps yield unknown source
locations. Boolean failed indices remain unknown. Missing release stays unknown;
an earlier failed release remains false even after a later successful record.
Missing PNG data produces needs_review/exit2 but keeps execution diagnostics.
Partial-effect uncertainty and the completed prefix remain in the retained report.

## H / T / D / C / U

H: existing read-only presentation preserves justified locations, outcomes and
uncertainty across input routes and compaction modes.
T: exact24 historical reports plus6 declared derivative controls,180 fresh CLI
processes, explicit source/input freeze, unchanged raw-only audit and8 controls.
D: all180 complete records, exact hashes/preserved reports/expected status and
uncertainty fields, no authority/task-success promotion,8 regressions and8 controls.
C: identical core presentation code explains parity; this is a regression of
existing semantics, not an algorithm improvement or new GUI efficacy result.
U: producer authenticity, current-world state, actual model recovery/calls/tokens,
latency/energy, arbitrary apps/OS and product qualification remain unestablished.

Exact variables, dimension checks and conditional reasoning are in frozen PLAN.md.
Source indices and counts are dimensionless; monotonic timestamps are same-host
order evidence, not calibrated physical latency or a benchmark. Environment is
Linux6.18.44/glibc2.41, CPython3.13.5, affinity0..4; no Docker image attestation.
Local sources are a verified subset, not a complete Git checkout. PYTHONPATH names
that subset explicitly; -S/-B is not -I isolation or a hostile-input sandbox.
Same-author separate auditor/code is not external human review.

## Complete records and chronology

Evaluation raw:1019890 bytes, SHA256
def5532fa1f1fd0fafcceecd2ab4035faffdaf70282cf0863f75e1efb13f9ef6.
Construction raw:161475 bytes, SHA256
5cedca8cea9fff66b5d2fa98f6731450697e92012e00f50674e1fe73ebedc10e.
Each raw aggregate retains every exact argv/stdin/stdout/stderr, PID, exit,
monotonic bracket, input/directory invariance and pre/post source map.
Base64 XZ parts are lossless transport only. All13 evaluation and5 construction
part Git blobs match local originals. They decode without invoking any old runner.

An initial input transcription error created unreferenced tree8a78c5f4... before
public freeze. It was not attached to the branch or executed. The unchanged input
bytes were then split into five checked parts; the data-only loader was adjusted
before the public freeze. This is not a safety block or a scientific retry.
PREFREEZE_TRANSPORT.json and the old loader are retained. The old construction
input file is exactly concatenated input_parts text plus one LF; its expected
hash is in the raw construction source_before map. All other source identities
are recorded there. Original construction results remain distinct.

After measurement, XZ packaging plus verify_publication.py were added without
changing any frozen source. This wrapper restores exact evaluation bytes into a
new temporary directory, re-encodes them for the unchanged frozen verifier, and
reproduces AUDIT/CONTROLS. It checks construction bytes/count, not a fresh
construction execution. The frozen first workflow runs8 regressions; its optional
plaintext records.b64 step is skipped for this compressed delivery. The new
separate evidence workflow actually runs verify_publication.py. No existing
workflow was modified. The consumed run_once.py is never run by CI.

## Read-only checks

From repository root:

```sh
python -S -B -m unittest -v runtime.cli_v1.test_review_compilation_r4k6
python -S -B research/integration/review_compilation_r4k6_v1/verify_publication.py
```

Do not invoke consumed run_once.py. The temporary parent and repository contents
are trusted; reconstruction is not an adversarial filesystem sandbox.

## Integration decision / remaining scope

For#2789 recovery, keep presentation completion, historical execution status,
source-operation mapping, completed prefix, partial-effect uncertainty and release
state separate. Existing code already provides the tested distinction. Merge only
after exact-head applicable checks and scoped review. GitHub CI, main merge and
external review are separate states, not implied by this local result. #3850/#57
and the global ROADMAP remain open. No blocked source/capsules from#4333/#4337/
#4322, foreign branch mutation, or production behavior change is included.
