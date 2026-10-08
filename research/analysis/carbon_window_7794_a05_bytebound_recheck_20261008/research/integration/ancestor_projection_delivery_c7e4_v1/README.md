# Ancestor projection: complete retained STOP evidence (#4317)

**Scientific disposition: HOLD_INCOMPLETE_30_CASE_LOCAL_PILOT.**
This is retrospective delivery of an already executed local pilot. No new GUI,
policy-worker or scientific allocation is run for this PR. Publication is NOT
preregistration and successful restoration is NOT scientific PASS.

## Question and result

Does checking the leaf suffice after an ancestor task is canceled? Conversely,
should every ancestor's own wait-for-child gate prevent the child from working?
The comparison changes only which ancestor conditions are required. The exact
original H/T/D/C/U, proof/variable table and report are retained in the capsule;
readable byte-identical copies are under `original/`.

| Fixed complete prefix, seven cases per policy | LOCAL_FRAME | ALL_ANCESTOR_GATES | ANCESTOR_LIVENESS |
|---|---:|---:|---:|
| Inputs after ancestor cancellation | 3 | 0 | 0 |
| Inputs without complete ancestry | 1 | 0 | 0 |
| Stable child completion | 2/2 | 0/2 | 2/2 |
| Total suffix / refusal | 6 / 1 | 0 / 7 | 2 / 5 |

These are descriptive counts from c00-c20, not the full30-case allocation or a
natural reliability estimate. The original schedule is five conditions x three
policies x two repetitions, six planned five-case batches. Canonical conditions:
STABLE, ROOT_CANCELED, MID_CANCELED, LEAF_CANCELED, ROOT_EVIDENCE_MISSING.

## Stop boundary, never repaired into PASS

21 complete cases, c21 partial, eight unstarted. c21 has a CANCELED_ANCESTOR
response and later app observation, then a3-second worker-exit TimeoutExpired.
The case supervisor records timeout and -15. Final CASE/actor exits and batch END
are missing. The outer tool timeout is also retained. Root cause remains unknown.
Do not infer successful shutdown from a response or from subsequent absence of a
process. No rerun, resumption, row replacement, pooling or post-freeze tuning.

The frozen full audit exits1:3369 checks,11 missing/completeness errors. The
frozen pilot-control wrapper remains blocked by that baseline, mutations0.
The separately named posthoc prefix audit returns3369 checks/errors0 and its
12 controls reject; it does not override the original failed acceptance gate.
All63 actor exits and final neutral input apply only to the21 complete cases.

## Exact retention and read-only reproduction

The16 binary parts restore all335 original study files /1959090 member bytes,
including construction, source, partial raw data, failed full audit and posthoc
code/results. No scientific row is sampled or regenerated. The334 original
manifest entries,308 first-outcome files and16 frozen sources are verified.

From this directory, CPython3.13 standard library only (no X11/Tk dependency):

```sh
python -B verify_publication.py
python -B -m unittest -v test_unpack
```

The verifier restores a new temporary directory and runs only the already
inspected read-only verifier. It requires exact audit output reproduction,
including the expected full-audit exit1 and blocked pilot-controls boundary.
To inspect without executing any source:

```sh
python -B unpack.py /tmp/ancestor-4317-new
```

Never launch the consumed run_case.py, run_batch.py or launch_batch.py.
Restoration requires a trusted destination parent and rejects existing paths,
non-regular/noncanonical archive members, hash/size/count mismatch and excess
expansion. It is not an adversarial-filesystem sandbox.

## Scope and integration decision

Private authenticated TCP-disabled Xvfb/Tk/XTEST, cooperative genuine per-frame
receipts except an explicitly withheld root record, three task levels, quiescent
state through dispatch. Ancestor registration/current snapshots are assumed
trustworthy and complete. No source authentication, dynamic parent discovery,
post-check cancellation, crash/distributed guarantee, physical HID measurement,
model/token/latency benefit, production runtime or root-task completion claim.
The separate auditor has the same author, not independent human review.

Inherited cancellation and an ancestor's own continuation conditions must be
kept distinct. This is bounded recovery evidence for #2789, not permission to
promote ANCESTOR_LIVENESS. The whole experimental allocation remains HOLD.

## Chronology and parallel ownership

Original local source freeze:2026-09-23T21:42:18.896807+00:00. GitHub publication
is later, under #4317. Intake main40493a9bb77eba00dd9d72207d683f2206ea45a5.
Own only research/ancestor-projection-retained-c7e4-20260924 and this additive
namespace. #4307/#4313 and their independent publication branches are untouched.
Old statements about write-tool unavailability remain historical, unedited.
The outer handoff ZIP and older nested ZIPs/patches are not duplicated here;
this capsule contains the complete335-file ancestor study, not every predecessor.

Roadmap: immutable restore/re-audit -> lossless delivery -> exact Git object
readback -> evidence PR -> exact-head review/checks -> qualified main readback.
No new science is authorized merely to turn HOLD into PASS. Global ROADMAP stays
open. A merged evidence PR is not runtime adoption or scientific acceptance.
