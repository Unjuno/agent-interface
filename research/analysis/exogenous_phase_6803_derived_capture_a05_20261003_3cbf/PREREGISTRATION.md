# #6969 derived-acquisition successor of #6803, allocation A05-3CBF-01

Owner: Codex thread `01a0b98d-3cbf-7710-b1a4-28c16e0b49da`.
Intake main: `6d7ce9693caae8c123fda532da64888f6006dcb9`.
Branch: `research/phase-6803-derived-capture-a05-3cbf-20261003`.
Allocation: `PHASE-6803-A05-ORBSTACK-20261003-3CBF-01`.
No modification or reinterpretation of predecessor raw evidence.

## H / T / D / C / U

H: A source-derived acquisition model responds to cue phase at a fixed capture
schedule. The original A04 classifier is insensitive to onset-only interventions
when supplied capture membership/downstream events are held fixed.

T: Closed integer intervals, capture schedule [10,50], observation horizon 60.
134 cells: expiry in {20,51,60}, onset in 0..expiry inclusive. Fixed-expiry primary
pair [9,20] vs [11,20], default delivery/decision latencies 1/1 and effect latency 0.
13 separately named controls cover absent cue, unsynchronized clock, late delivery,
late decision, disabled effect, safe stop, right censor, effect after expiry,
horizon before capture, expiry equality, zero-latency equality and fixed-duration
phase pair [9,11] vs [11,13] with zero downstream latencies.
Candidate inputs contain no membership, events, expected verdicts or receipt labels.
Every acquisition and downstream event is generated inside execution.

D: PASS_METHOD_SCOPED requires all 147 rows to exactly match the independent
finite-set oracle, both matched contrasts to produce eligible_effect_in_model vs
not_acquired, all 10 frozen copied-output mutations to be rejected, and all four
original-source onset probes to match their two insensitive pairs. Source hashes,
mount custody and container exits/observed resource limits must also be verified.
Any failure remains FAIL_METHOD, FAIL_AUDIT or STOP; no same-allocation rerun.

C: The original primary pair also varied supplied acquisition and downstream
events; it cannot isolate onset. This successor isolates onset in the primary pair,
but that changes duration; the fixed-duration translated pair is distinct.
All arithmetic is exact integer time, not physical timing. Delivery and decision
must occur by cue expiry; a timely decision may cause a modeled effect after
expiry if observed by horizon. This is an explicit retained deadline convention,
not a universal task requirement. Censoring precedes a negative classification
when expiry has not elapsed and no modeled effect/stop is observed.

U: Zero authority and live effect events. No real receipts, model, GUI, input
device, human-tempo, economic, safety, O3/O4 or #59/#57 completion claim.

## Independent audit and controls

The auditor imports none of candidate.py, prepare.py or legacy_probe.py. It
reconstructs the exact finite input domain separately and computes cue membership
by intersecting integer active-time, capture-time and observed-time sets.
It reconstructs every downstream timestamp and verdict. Canonical JSON comparison
distinguishes bool, integer and float representations. Its ten copied-output
controls are drop-row, duplicate-row, wrong-phase-verdict, forged-capture,
shifted-source-echo, altered-schedule, wrong-decision-time, forged-effect-token,
boolean-time-alias and authority-claim. Mutant outputs and rejection diagnostics
are retained, not used to tune candidate code after formal execution.

The separate legacy diagnostic mounts pinned original candidate/fixture plus
legacy_probe.py, changes only onset in c01 (9->11) and c02 (11->9), and records
all four full inputs and classify tuples. It is not an A04 formal replay. The
auditor independently checks the four inputs and tuples against authored literals.
Construction unittest calls are separate from these formal invocations.

## Runtime and invocation freeze

Use this task's private `research-6183-t0-20261003` Ubuntu arm64 VM, not the
OrbStack default/shared Docker endpoint. Cached image:
`python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`.
No image pull/package install; Docker --pull never, network none, CPU 1, memory
512MiB, UID/GID 501:501, read-only root, all capabilities dropped, no-new-privileges.
Candidate source mount has only candidate.py and fixture.json. Legacy and auditor
mounts are separate. Auditor consumes candidate/probe outputs read-only.
runner.py freezes exact command arrays, checks absent output/container names and
hash custody, marks the allocation consumed before invocation, retains inspection,
stdout/stderr and cgroup limits, and stops immediately on a nonzero exit.
Exactly one formal candidate, legacy diagnostic and auditor invocation each;
construction tests may be run before the source freeze and are not formal data.

Formal outputs have a fresh `phase-6969-a05-3cbf` guest path and local `formal/`.
No old allocation paths are reused. Source SHA256s bind FREEZE.json; publish its
Git commit to the Issue before execute. Source/image/fixture/gates cannot change
after this freeze. Any later methodological change needs a new allocation.

## Roadmap and handoff

1. Preserve #6803 snapshot-only evidence and the post-merge audit finding.
2. Construct/freeze source-derived cells and separate independent oracle.
3. Execute the private container sequence once; retain PASS/FAIL/STOP and limits.
4. Publish exact scoped results in #6969, #6803 and coordinating #6957, then PR.
5. Keep native/physical/live acquisition validation and #59/#57 integration open.

Nearby closed #6749 already contains ordered-prefix successor experiments with
different frozen policies; do not duplicate or pool their counts with #6809.
The overall repository roadmap is still incomplete. This package addresses one
specific method gap, not end-to-end interface viability.
