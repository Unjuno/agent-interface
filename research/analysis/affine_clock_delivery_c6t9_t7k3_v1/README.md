# Retained affine-clock deadline contract — #4363

## Disposition and chronology

**PASS_LOCAL_AFFINE_CLOCK_CONTRACT**, retained from the already completed
conversation-local `affine-clock-c6t9-20260925-01`. This is retrospective evidence
delivery, not a new experiment or public preregistration. No new full-corpus
candidate evaluation, GUI/input, clock calibration, or model/provider call was
performed during delivery. Original source, result, failure and STOP files remain
byte-identical, including historical `github_writes=0` / `main_integrated=false`
statements and the first monolithic publication-verifier timeout. Those statements
describe the original session, not the later publication of this directory.

The local source/input/proof freeze preceded the original single evaluation.
The synthetic clock coordinates are exact rationals, not measured timestamps.
The supplied Linux x86_64 / CPython 3.13.5 environment has no Docker/OrbStack image
attestation. No broad runtime, physical-clock, task-success or performance claim.

## Question and retained result

When rate and offset are simultaneously constrained by calibration intervals,
keep the joint feasible clock family while translating a logical release interval.
Do not substitute one fitted clock for all compatible clocks. Independent
marginal intervals remain conservative but can lose useful decision precision.
This is elementary interval/linear-optimization reasoning, not a new clock scheme.

| Original fixed input classification | Count |
|---|---:|
| ON_TIME | 3842 |
| LATE | 1951 |
| UNRESOLVED | 626 |
| Inconsistent clock family | 2661 |
| Invalid/missing/out-of-scope input | 8 |
| Total | 9088 |

The nominal comparator over-certifies ON_TIME in141 and LATE in66 inputs. The
marginal-box comparator remains conservative but loses164 otherwise decisive
classifications. These counts are not real deadline failures, failure probabilities,
or paired independent experimental samples. The unchanged raw auditor reports
110731 checks, errors0;16 unit methods and12 effective evidence mutations pass.

## H / T / D / C / U

H: a positive affine relation valid over the entire declared horizon and a
nonempty joint feasible set give the tight conditional release interval.

T:9072 fixed combinations plus16 directed boundaries; exact Fraction arithmetic;
candidate eliminates an axis and optimizes envelopes, separate auditor enumerates
2D boundary intersections without importing the candidate. One original evaluation.
This delivery only reconstructs saved bytes and runs read-only checks.

D: original PASS requires all9088 rows, exact source/process provenance,
independent algorithm agreement, empty/invalid rejection, open/closed endpoints,
no input/task authority,16 tests and12 effective corruption controls. Delivery
additionally requires all81 original files to restore byte-for-byte and all
readable copies to match. Applicable exact-head CI and review are separate gates.

C: finite calibration agreement does not establish affine behavior between samples.
The original proof retains an explicit monotone non-affine counterexample.
Point-estimate and marginal comparators are authored, not alleged deployed defects.

U: real calibration/drift/quantization, suspend/restart, authenticated clock identity,
multiple transitions, physical HID, hard-time guarantees, model/task/token/latency
benefit and production promotion remain untested. Exact arithmetic is not physical
accuracy. No calibrated combined uncertainty or coverage factor is invented.

Read [the complete original proof and variable/unit table](original/PROOF.md),
[plan](original/PLAN.md), [freeze](original/FREEZE.json), and
[original result](original/SUMMARY.json). All six original Python sources are
readable under `original/source/` as well as retained in the capsule.

## Complete lossless evidence, not digest-only retention

The capsule restores **all81 original files /9465087 bytes**, including all9088
input/output rows, source, process receipts, construction tests,12 original control
results, audits, the earlier failed packaging attempt, and original manifests.
No prior study archive or unrelated blocked publication is imported.

- Original conversation ZIP373685 bytes, SHA256
  `81baad5a571fc46f1008c98ed0f1d479b92d86eee974b87f731a4c2109621f68`.
- Capsule52664 bytes in13 binary parts, SHA256
  `d34c4f41d849003bc104769f2631857fac6a6828aafead76f731c4e210f6dcd5`.
- Intermediate tar9615360 bytes, SHA256
  `01fcedc26806db5dac093eaa9c9f573367f170a6da246b41023c0c2968349bad`.

Saved JSONL objects are losslessly encoded into typed columns, including every
saved input and output value; restoration does NOT call the candidate, regenerate
answers or infer omitted outcomes. Canonical JSON rendering must reproduce the
original input/raw hashes. A redundant first-delivery ZIP is reconstructed from
its retained member bytes and complete ZIP metadata, then checked against its
original hash. This last exact-byte step requires DEFLATE9 output compatible with
zlib1.3.1; a differing byte stream is refused rather than silently accepted.
The original outer conversation ZIP itself is identified, not reconstructed;
all81 of its member files are reconstructed exactly.

`CAPSULE.json` binds every part and the expanded representation. `unpack.py`
limits expansion and member count, accepts regular canonical relative files only,
and verifies every original size/hash before writing. It never executes archived
source. Publication files and the destination parent must be trusted/quiescent;
this is not an adversarial filesystem sandbox or source-authentication guarantee.

## Read-only verification

From this directory, CPython3.13 standard library and compatible zlib:

```sh
python -B verify.py
python -B -m unittest -v test_unpack
python -B verify.py --control 0
```

The optional control index is0..11; run each in its own bounded invocation.
`verify.py` uses a fresh temporary destination and executes only the unchanged
retained read-only verifier. It checks readable copies, original hashes, the
110731-check saved-data audit and16 unit methods. A selected control replays one
saved mutation and requires its output to match the original. Do NOT run
`original/source/run_check.py` or the restored consumed allocation launcher.

`REVALIDATION.json` retains actual command/exit/clock receipts and outputs for
baseline, all12 saved controls, fresh restoration and12 new packaging tests.
Read-only reruns do not create new scientific samples. Same-author separately
structured audit and self-review are not independent human approval.

## Ownership, roadmap and integration decision

Intake main `4a1f3957e91b412a64769199f78f2c4b0102d28b`; owned branch
`research/affine-clock-retained-c6t9-20260925-t7k3`. Only this additive directory
is changed. README/current-goal/roadmap, recent open/closed Issues, open PRs,
first100 branches and targeted affine/c6t9 searches were inspected; bounded,
non-atomic searches cannot establish absence of unpushed work. #4345 and other
foreign allocations remain untouched.

Roadmap: immutable verification -> complete permitted publication -> exact Git
object readback and fresh restoration -> evidence PR -> exact-head applicable
checks and scoped review -> qualified main merge/readback -> dependency-safe
owned-ref cleanup only when supported. No scientific rerun to improve delivery.

Concrete #2789 recovery/measurement decision: do not issue a definite deadline
claim by collapsing a feasible clock family to one nominal clock. Preserve the
joint model when justified; otherwise retain uncertainty. Neither output grants
input authority or task success. No existing runtime was promoted or changed.
#3880's real OrbStack calibration gate, #1859, #57 and global ROADMAP remain open.
