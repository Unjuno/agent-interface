# Run log — Issue #6604 T0

## Host construction only

The following host-side executions validate that the frozen fixture, candidate, and independent auditor are wired correctly. They are explicitly **not** the formal container allocation and do not prove the T0 result.

Commands, from the repository root:

```text
python3 -m unittest discover -s research/analysis/disturbance_timescale_6604_t0_v1 -p 'test_*.py' -v
python3 research/analysis/disturbance_timescale_6604_t0_v1/candidate.py research/analysis/disturbance_timescale_6604_t0_v1/cases.json research/analysis/disturbance_timescale_6604_t0_v1/construction_host/candidate.raw.json
python3 research/analysis/disturbance_timescale_6604_t0_v1/audit.py research/analysis/disturbance_timescale_6604_t0_v1/construction_host/candidate.raw.json research/analysis/disturbance_timescale_6604_t0_v1/cases.json research/analysis/disturbance_timescale_6604_t0_v1/oracle.json research/analysis/disturbance_timescale_6604_t0_v1/construction_host/audit.json
```

Results: construction tests 8/8 PASS; candidate emitted 14 rows; separate auditor reported `PASS_METHOD_SCOPED`, rows=14, errors=0. Raw SHA-256 `c752b037630234f01565be9f0ca9af4bd79421ef533c9c244445e0200904bdc6`; audit SHA-256 `4b752f6d261ac57edbf57dde2e0598acfefbf207a644bb01742c3718932a3b57`.

Observed fixture scores: slow drift direct=16/local=10; fast reversal direct=45/local=59; pooled planted matrix direct=61/local=69 (so pooling chooses direct despite local winning slow). No-crossover pair direct=63/local=31 and both constituent schedules favor local. The semantic-swap case is deliberately omitted from the semantic-effect claim. These are host construction outputs from a planted deterministic fixture only.

## Construction correction: opaque case IDs

Review found that the first host package exposed descriptive scenario names in candidate-visible case IDs. Although the candidate did not branch on those names, this leaked the semantic-swap condition and weakened the unobservable-alias control. The first raw/audit pair above is preserved unchanged as the initial construction outcome. No formal invocation had occurred.

The source was corrected to opaque IDs `C01`–`C07`; scenario labels and hidden semantic-swap truth now exist only in scorer-only `oracle.json`. The same candidate/auditor case matrix was rerun into the distinct `construction_host_v2/` path. Candidate emitted 14 rows and independent replay returned `PASS_METHOD_SCOPED`, 14 rows, zero errors. Construction suite: 9/9 PASS. Final-source raw SHA-256 `df8d65b7c9f5c32df075c254ad708530bfe27af061bb3269dd1fba6e4ba1c14b`; audit SHA-256 `4b752f6d261ac57edbf57dde2e0598acfefbf207a644bb01742c3718932a3b57`.

During this correction, one host development test run failed two checks because the test still referenced the descriptive case ID and incorrectly expected only two rows in a seven-case dictionary. The test selectors were corrected to opaque ID `C02`, and the invalid cardinality assertion was removed. The complete suite passed 9/9 before the final-source construction candidate/auditor run. This is retained as a test-harness setup failure, not scientific evidence. The semantic source correction and all first-pass artifacts remain explicit; no formal candidate or auditor was consumed.

Additional construction hardening checks now explicitly reject descriptive case labels in candidate input, assert the semantic-swap observation stream aliases the slow control, verify per-stratum versus pooled ranking, and validate the terminal release receipt. Final-source construction tests pass 11/11. Candidate and independent auditor were executed once more to the distinct `construction_host_v3/` path; the raw and audit hashes remain byte-identical to v2 (`df8d65b7c9f5c32df075c254ad708530bfe27af061bb3269dd1fba6e4ba1c14b` and `4b752f6d261ac57edbf57dde2e0598acfefbf207a644bb01742c3718932a3b57`), with 14 replayed rows and zero errors. Formal container invocations remain zero.

## Formal container allocation

Candidate=0, auditor=0, retries=0. No container was started: at the fresh OrbStack inventory, unrelated container `unjuno-native-ci-6092` remained Up; `docker stats --no-stream` reported 0.00% CPU and 112 KiB / 15.66 GiB. Low utilization is not owner release or an allocation. No stop, exec, mount inspection, or modification of that container was performed. Formal T0 remains `HOLD_SHARED_ORBSTACK_LANE_UNASSIGNED` pending an explicit conflict-free runtime slot; do not interpret host construction as a container result.

## Successor allocation 02 — isolated OrbStack Docker (2026-10-02)

Allocation 01 above remains preserved as an unconsumed shared-engine HOLD. To execute the same Issue hypothesis without the shared daemon, successor allocation `DISTURBANCE-TIMESCALE-6604-T0-ISOLATED-ORBSTACK-20261002-02` used dedicated isolated OrbStack machine `agent-interface-6604-t0-isolated-20261002` with its own Docker daemon. The exact source hashes, current-main SHA, machine/image identity, and one-shot commands are frozen in `SUCCESSOR_ISOLATED_ALLOCATION_02.md` and its companion JSON freeze.

Pre-run gates passed: main and branch were `7d7f2f1a1ff281c68c9864ae1c56aa5f68b35ae0`; no competing #6604 branch or PR was found; source/input hashes matched; image digest/platform matched; output directories and dedicated Docker daemon were empty. Candidate container ran once, exit 0, log `rows=14 status=COMPLETE`; raw hash `df8d65b7c9f5c32df075c254ad708530bfe27af061bb3269dd1fba6e4ba1c14b`. Independent raw-only auditor ran once in a second network-disabled container, exit 0, `PASS_METHOD_SCOPED`, 14 rows, zero errors; audit hash `4b752f6d261ac57edbf57dde2e0598acfefbf207a644bb01742c3718932a3b57`. Retries=0. Exact IDs, commands, inspect settings and timestamps are in `formal_02/RUN_RECORD.json`; outputs and interpretation are in `formal_02/`.

Docker inspect confirmed the requested `--network=none`, read-only rootfs, source/raw mounts, 0.25 CPU, 512 MiB, and 64-PID configuration. The isolated machine itself is configured 1 CPU / 2 GiB, but its nested Docker daemon reports 10 CPUs / about 15.7 GiB; no effective host or per-container resource enforcement is claimed. The result is method-scoped to the deterministic synthetic schedule; it is not a live Agent Interface route-benefit result.
