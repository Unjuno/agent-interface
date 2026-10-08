# Issue #4062: two-reader retention-lock ownership

## Result and scope

**PASS_READER_LOCK_OWNERSHIP_SCOPED** from one prospective 18-case allocation.
This is research evidence only. No shared runtime, production collector, CLI,
workflow, dependency, or global research direction is changed. The finite
allocation is complete; the repository-wide roadmap is not.

| Lock ownership | Cases | Exact remaining-reader results | Early reclamation |
|---|---:|---:|---:|
| Independently opened locks, explicit unlock | 6 | 6 | 0 |
| Shared open description, close-only release | 6 | 6 | 0 |
| Shared open description, explicit unlock | 6 | 4 | 2 |

Both directed SHARED_UNLOCK/FIRST_RELEASE cases let the collector remove the
source while reader B remained unfinished. B correctly returned SOURCE_GONE
without exposing a cursor or record. This is an availability/retention failure,
not wrong-data delivery or a fresh-action-authority result. All initial collector
probes deferred; all final probes left both generation child files absent.

Integration constraint: independently releasable logical leases must not share
an explicitly unlocked open file description. Independently opened locks passed
this fixture; close-only shared ownership is a collective lifecycle, not a
universal substitute for per-reader leases. The original single-reader worker's
close-only behavior is unchanged and is not classified as defective.

## H / T / D / C / U

H: A's explicit unlock of a shared description can remove B's retention protection;
independent opens or shared-close-only ownership retain protection until all
relevant readers finish. Known Linux flock semantics predict this behavior.

T: Three ownership modes, three barrier-directed schedules (both hold, A releases,
A exits with registered code 73), two repetitions: 18 fresh private cases in two
one-use nine-case batches. Each has two reader processes and one collector.
Reader.prepare/read and Collector.collect are inherited unchanged from the exact
prior worker; the small adapter varies lock acquisition/release ownership only.
The parent closes its shared-descriptor copies before reader preparation.
Construction's nine cases are excluded. No formal reruns, substitutions or pooling.

D: The expected two unsafe-control source losses, 16 exact B reads, all initial
probes deferred, final reclamation in all 18 cases, all source/response/cursor/
observer/process identities, actual outer exits and 10 corruption controls must
reconcile. The raw-only audit performs 3,896 checks, returns no errors and rejects
10/10 mutations. SHARED_UNLOCK remains a rejected ownership policy even though
the boundary hypothesis passes. Missing evidence would be HOLD/STOP, not PASS.

C: Stable lock inode, cooperative collector, immutable child bytes, local Linux
filesystem, no arbitrary descendants or lock-file replacement. flock is advisory
and bound to an open file description; dup is not an independent open. This is a
pinned Reader/Collector composition study, not a new OS theorem or vulnerability.

U: No model/provider, GUI/input, network experiment, package installation, user
files or production mutation. No latest-state authority, ACK/model consumption,
power-loss durability, fairness, starvation, cross-platform or task/token/latency
benefit is established. Timings are ordering diagnostics, not benchmark estimates.
The auditor is separate code/process by the same author, not external review.

## Freeze, execution and evidence

Intake main: 2308b8301d69b7089a2e0636486736ed59b61537.
Own branch: research/retention-lock-ownership-6c2f-20260922.
The ten source/plan/environment SHA-256 values were publicly frozen before formal
execution at commit 0afeece5942e4f95881bce8ff0c89a44a14aee72 and Issue #4062 comment
5768694280. Full source bytes are published here after execution, not claimed to
have been remotely available before the hash freeze. The source freeze is unchanged.

FREEZE SHA-256: 0d6bafcd1be8383c47cf1a34649d101b136feb42e5380b52551a94dd8f27739c.
AUDIT SHA-256: 1b79403df9cdc510026c52f1fc7bcdf8fe0436b59a370bb6e44e19b5637392d6.
Two actual batch run/outer exits are 0; independently captured stderr is empty.
All 54 workers were waited: 48 ordinary exits 0, six registered A exits 73.
Four new construction-test methods pass. Formal first outcome is recorded in
Issue #4062 comment 5768701386.

Actual environment: supplied Linux x86_64 execution container, CPython 3.13.5.
Docker and gh CLI are absent. No Docker Desktop/OrbStack or image-attestation
claim. Complete machine/source identities, commands, snapshots and child/outer
receipts are retained in the capsule, including the original full prior worker,
upstream reader and DeliveryLedger.

## Retrospective prior evidence: separate 48-case allocation

This capsule also publishes all 643 original files from the previously uploaded
`generation-retention-20260922-01` study. They were locally frozen before execution
but were not GitHub-preregistered; this publication is retrospective. All original
bytes, local publication HOLD and overlap disposition remain unchanged.

Three old path/directory/file-descriptor policies partially overlap #3978/PR #4024.
They are retained overlapping evidence, not 48 independent new discoveries.
Its one-reader shared-lock arm motivates the new two-reader question. The old 48,
new 18 and #3978's 63 cases are never pooled. #3995/PR #4016 addresses read-offset
sharing, not retention-lock release. No predecessor files are edited.

Prior audit SHA-256:
d9402006cba4e65468dc3575bfca073ad285e60d72867daae5d9f81ec2ed2bae.
Its eight tests and 15 original audit corruption controls pass when re-read.
Historical files saying #3876 remained open are retained verbatim for provenance;
#3876 is already closed and this work does not reopen it. PR #3964 was previously
merged by other work, not this continuation. Only Issue #4062's scoped allocation
is eligible for completion through this PR.

## GitHub-only read-only reproduction

The 18 binary parts concatenate to a 107,044-byte XZ capsule with SHA-256
`d235cda9161e026a56979e23468ecae23a7fe1c1b310b133bc83175770e3319e`.
Expanded UTF-8 file-map JSON is 3,736,407 bytes and contains 784 exact files.
CAPSULE.json records every part's SHA-256, Git object ID and size. This encoding
is evidence transport, not an executable dependency. unpack.py verifies all
bounds/hashes/paths before creating a new output directory and executes no study.

```bash
python -S -B research/integration/retention_lock_ownership_6c2f_v1/unpack.py /tmp/retention-4062-new
python -S -B /tmp/retention-4062-new/current/audit.py /tmp/retention-4062-new/current
python -S -B /tmp/retention-4062-new/previous/audit.py /tmp/retention-4062-new/previous/formal-01 --controls
```

Use a genuinely absent directory. Do not invoke run.py or execute.py with a
consumed formal allocation. Source for review is under current/ (worker.py,
prior_worker.py, run.py, execute.py, audit.py, test_contract.py and upstream
modules). Full H/T/D/C/U and the variable/unit table are in current/PLAN.md.
Previous raw/source is under previous/; old publication context is separate.

Local fresh restoration matched all 784 files. Both re-audits returned exit 0
and stdout byte-identical to their respective original audits. New four and old
eight tests passed. Package controls reject existing destination, bit flip,
wrong part order, wrong file count and invalid expansion bound. See
PUBLICATION_CHECK.json; this is not a remote CI or external-review claim.

## Retained engineering incidents

An earlier old-test discovery command treated -v as a corpus path; corrected
direct invocation passed. The visible traceback and limitation that the full
failed output was not separately saved are retained. The container tool emitted
a TERM-variable message outside captured study stderr; it did not justify a rerun.
The first package checker compared old audit stdout to a metadata receipt, failed,
and was corrected to the actual old AUDIT.json. Only the postformal comparison
path changed; no frozen source, raw evidence, scientific gate or verdict changed.
All such engineering corrections remain under this Issue, not new successors.

## Delivery and next gate

All changes are additive in this namespace. Exact-head review/checks and main
readback remain separate delivery gates until confirmed in the PR. Do not infer
CI or production success from local PASS. Only dependency-safe own-branch cleanup
is permitted after verified integration. Further work should address an actual
selected producer/host's retention and useful-feedback requirements, not generate
more isolated lock studies or wrapper-only successor Issues.

Primary implementation specifications:
- Linux man-pages flock(2): https://man7.org/linux/man-pages/man2/flock.2.html
- Python 3.13 fcntl: https://docs.python.org/3.13/library/fcntl.html
