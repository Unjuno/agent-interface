# Retained gap-deadline wait experiment — Issue #4031

**Retrospective evidence publication.** This directory delivers the already
completed `gap-deadline-wait-20260922-formal-01` allocation. It is not a new
experiment, GitHub preregistration, or production implementation. Parent #3986
and PR #4004 remain unchanged.

The original `RESULT.md`, `PLAN.md`, source, local freeze, construction failures,
raw journals/databases, process exits and original audit are retained verbatim.
Statements in those original files that GitHub publication was unavailable
refer to the earlier session. Issue #4031 and this delivery were created later;
the historical documents have not been edited to manufacture preregistration.

## Scientific result and integration meaning

`PASS_WAIT_SCHEDULING_BOUNDARY_SCOPED`: 30/30 cases, 666 worker journal rows,
252 pipe commands; one formal orchestration and zero retries/replacements or
post-freeze source changes. Every worker and the formal orchestrator have
retained actual exit code 0. The separate raw-only auditor rejects all 12
semantic corruption controls. Nine original unit methods pass.

Both research comparators invoke the same unchanged elapsed-time GapPolicy.
Restarting an 80 ms relative wait on every incoming message changes the tested
quantity from elapsed gap age to inactivity age. Holding the first unresolved
gap's deadline avoids that deferral. Neither method can execute while its event
loop is blocked. The 80 ms value is diagnostic, not a production default.

See the original [result](RESULT.md) for medians/ranges and all five conditions,
and [plan](PLAN.md) for H/T/D/C/U, variable definitions, units, conditional proof
and scope. `worker.py` is the directly readable tested wait implementation.
The full runner, independent auditor, tests and evidence are in the capsule.

The concrete integration constraint is to distinguish a gap-age deadline from
an inactivity timeout, and to state which execution availability the delivery
claim assumes. This PR changes no shared runtime or producer/host route. It does
not claim physical release, host presentation, model consumption, task success,
latency/token benefit, hard deadlines, production adoption or global roadmap
completion. The same-author separate auditor is not independent human review.

## Exact retained bytes

`PACK.json` binds 12 ordered binary fragments to one bounded lossless XZ
file-map capsule. It preserves all **265 original files / 2,118,526 file bytes**,
including the original `SHA256SUMS` with 264 entries. Readable copies in this
Git directory are for review; use the unpacked directory for original checks.

- Original conversation ZIP: 250,824 bytes; SHA256
  `cfcf3d30cb27b678400fdefd65f252a6b13560e44d20fc64ded548195125f6f5`.
- Delivery capsule: 70,032 bytes; SHA256
  `6244a90364b261ffdc1766727e76dda9344f9c3a2c52d020966b3f55c47b439e`.
- Original audit SHA256:
  `e666a9cd3e5395fd9e0908afb782912a2c34b63cd0c1e9eddec5befbae8d31c9`.
- Original local freeze SHA256:
  `f894a46cfcb893d873a1dbb15f5f8145ed3b7fd39b3a12d6f889d53c197830eb`.

The capsule is not a byte-identical copy of the ZIP container: it restores the
same original member names and bytes. Hashes attest integrity, not authenticity.
All 12 GitHub-created binary blob IDs matched the locally computed object IDs.

## Read-only verification

Run from this published directory, with **new** output destinations:

```sh
python -B unpack.py /tmp/gap-wait-review-4031
cd /tmp/gap-wait-review-4031
sha256sum -c SHA256SUMS
python -B -m unittest -v test_contract
python -B audit.py --root formal-01 --schedule formal_schedule.json \
  --freeze FREEZE.json --out /tmp/gap-wait-audit-4031.json
cmp AUDIT.json /tmp/gap-wait-audit-4031.json
python -B audit.py --root formal-01 --schedule formal_schedule.json \
  --controls --out /tmp/gap-wait-controls-4031.json
cmp CONTROLS.json /tmp/gap-wait-controls-4031.json
```

Use Python with its standard library and SQLite; the original execution and
current verification used CPython 3.13.5 / SQLite 3.46.1 on Linux x86_64. Do not
use `python -O`, which disables assertions used by the original auditor/tests.
The unpacker only writes data and never imports an experiment, opens a display,
or starts a worker. Use trusted source/destination parents with no concurrent
mutation. A write failure may leave a partial fresh destination; inspect it
rather than overwriting or reusing it silently.

**Do not run `run.py` or consume the old formal allocation again.** Read-only
reconstruction is not another formal run. Any scientifically justified new
allocation needs a separate prospective freeze, explicit deltas and fresh
output identity; an upload/timeout incident alone does not justify new science.

## This continuation's checks and preserved limitations

`PUBLICATION_REVALIDATION.json` records original checksum, unit, raw-only audit
and semantic-corruption checks. `PUBLICATION_CHECK.json` records fresh capsule
restoration, equality of all 265 files, repeated original checks, and nine
packaging refusal controls. Both audit and corruption reports after restoration
are byte-identical to the originals. New formal invocations in this continuation:
**zero**. Packaging tests are engineering checks, not new scientific samples.

The earlier combined outer tool timed out only after the formal process had
returned and its exit records were retained. The original incident, separate
read-only audit process and first dispositions remain inside the capsule.
No missing scientific rows or process exits were inferred from a summary.

The source experiment ran in the supplied Linux execution container, with an
AMD EPYC 9V74 guest, unpinned frequency/load, EpollSelector and CLOCK_MONOTONIC.
No Docker/OrbStack engine/image attestation or cross-platform equivalence is
claimed. It used no model/provider, GUI/input, user desktop, credentials,
external-network experiment or shared runtime mutation. Software clock
resolution is not calibrated timing accuracy.

Publication intake main was `1f798cbb60b929e738c6bf8a5912470b38b45ff4`.
Repository direction, recent open/closed Issues/PRs and 123 branch names were
reviewed; exact-name wait-study searches found no duplicate. This bounded
inspection cannot rule out unpushed work. All changes are additive under this
study path; concurrent unrelated work is untouched. Repository CI/review and
main integration are separate gates, reported on the PR rather than inferred
from these local tests.
