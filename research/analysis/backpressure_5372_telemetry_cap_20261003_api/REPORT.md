# #5372 telemetry and authoritative queue cap — first result

**Disposition: SUBSUMED_BY_AUTHORITATIVE_CAP_SCOPED.** For this exact finite
single-owner unit-job model, an atomic pending-work cap is sufficient. Delayed
or faulty telemetry adds no completion advantage to that cap. Retain the simple
cap as the baseline for any later distributed/heterogeneous queue study; do not
add a new production backpressure layer based on this result.

One candidate and one separate raw-only auditor ran on 2026-10-03,
12:06:02–12:06:03 UTC, both exit 0, retries 0. Source freeze commit
`35ee2a1` precedes execution; exact base is
`a472e7e2fd474a95fbce4d9d59132ca83cd67c94`. Full file identifiers, source
hashes and prospective thresholds remain in FREEZE.json and PLAN.md, unchanged.
This is a new analytical construction of #5372's misreported-telemetry boundary,
not T1, route-expansion A01, or the invalid/unaudited A02.

## Observations

6,561 paired finite conditions, four arms (26,244 traces), eight ticks each.
Each arm sees exactly 32,805 offered jobs across the exhaustive corpus. The
aggregate totals are enumerated workload counts, not sampled-population estimates.
Report modes and redundant delays are intentional factorial controls; no
frequency/probability estimate follows from their equal weighting.

| Policy | Verified synthetic jobs | Explicit UNKNOWN | Cap violations (cases) | Maximum pending | Cases pending after drain |
|---|---:|---:|---:|---:|---:|
| Report only | 18,421 | 13,514 | 2,251 | 9 | 531 |
| Report + actual cap | 14,841 | 17,964 | 0 | 2 | 0 |
| Actual cap only | 22,797 | 10,008 | 0 | 2 | 0 |
| One admission/tick + actual cap | 19,710 | 13,095 | 0 | 2 | 0 |

Report-only admitted 19,291 jobs: 18,421 finished and 870 remained pending.
Those pending jobs are retained explicitly, not excluded from the offered-work
denominator or relabelled as completed. Every cap-based arm drained all admitted
jobs. All arms retained and serviced the fixture's 52,488 mandatory safety
events on its dedicated lane; this is synthetic identity/accounting evidence,
not physical key release or an observed real scheduling guarantee.

CAP_ONLY never completed fewer jobs than REPORT_CAP (0/6,561), and completed
more in 2,535 conditions. It never completed fewer than RATE_CAP and completed
more in 2,601 conditions. No hypothesis of a sophisticated controller's
superiority was adopted. The constant-HIGH fault causes REPORT_CAP to refuse
all work even when its actual queue is empty; the capacity-only baseline
does not depend on that untrusted signal.

The first overflow witness in audit.json is arrivals `[0,0,0,1,2]`, honest
reports delayed one tick, ALTERNATE service. At tick 3 one job enters and service
is disabled; tick 4's report still sees the earlier empty queue, admits two more and reaches
occupancy 3 before service. The local within-batch report increment is present;
this is a stale-snapshot boundary, not unlimited same-batch admissions.

## Validation and evidence

The independently coded list-based reference imports no candidate code and
reconstructed every offered identity, report, admission/refusal, normal service,
pending list, peak and dedicated-lane event exactly. All six value-changing
controls were rejected: missing offered record, forged completion count,
hidden peak, lost safety, wrong report and foreign-task completion. This is
implementation diversity under one author's supervision, not nonauthor review,
independent research assumptions or FINAL-v5 merge approval.

Original raw SHA-256:
`469e411a3a301396a96ce7526503174d114fdb1b0108494d5c5178046e7facc8`.
The original 26,762,476-byte raw remains locally available. The published gzip
archive was decompressed and checked byte-for-byte before delivery. RUN.json
retains original stdout/stderr hashes, actual argv/UTC/exit, Python and host.
ARCHIVE.json records the lossless storage transformation separately; no original
raw, frozen source, decision or run record was changed by compression.

Environment: Linux 6.18.44 x86_64/glibc2.41, CPython3.12.14, stdlib only,
one child at a time. Host cgroup reports 16GiB memory.max and CPU quota
400000/100000; child requested RLIMIT_AS512MiB/CPU60s/file64MiB. No memory-limit
stress test, GPU, WSLc, Docker allocation, GUI, model, native input or network
was part of the numerical run. Candidate/auditor elapsed values in RUN.json
are launcher accounting only (single observations), not performance evidence.
No CPU hardware model or uncontended-load performance claim is made.

Applicable local checks: hand-derived construction controls passed before
freeze; full raw reference and mutation checks passed in the sole auditor;
saved evidence/archive/source integrity and diff formatting are checked at
delivery. The repository's index check is applied with its documented sparse
checkout behavior; unrelated runtime/backend suites and remote CI results are
not claimed. Evidence code is outside promoted runtime, has guarded CLI entry,
and its construction file is not named for automatic unittest/pytest discovery.

Setup-only incident: the initial depth-1 full clone was stopped by its owner
after growing past2GiB without a checkout; a filtered sparse clone provided
the exact committed source and required guidance. No candidate/auditor was
running during this setup change. The incomplete clone contains no research
evidence and is not an experiment outcome or fleet-wide availability result.

## Limits and next decision

Atomic authoritative count and enqueue are assumed. Jobs are homogeneous and
single-threaded, with no separately occupied in-flight server slot, retries,
freshness deadlines, remote ownership, or recovery obligations. If pending work
is distributed, a real central reservation or credit mechanism must be shown;
a report of pending count cannot stand in for one. The dedicated safety lane
does not test overload or common-cause failure of cleanup itself.

Next useful integration check: inspect the selected actual verifier path for
an atomic pending reservation that covers queued AND in-flight work, and verify
release/cancellation accounting with a targeted race regression. Only a concrete
residual there justifies a new mechanism or live allocation. No runtime change
or new resource authorization is inferred. #5372/#57/#59 and the live-control
goal remain open. Main delivery still requires FINAL-v5 nonauthor agreement.
