# Archival qualification: #5776 recovery-rate T0 source and reported host failure

This is an additive preservation note for the five unchanged published files from [Draft PR #5788](https://github.com/Unjuno/agent-interface/pull/5788), head `b9f6384f8577a0c14a9845df273a7199f08c56b5`, branch `research/5776-recovery-rate-t0-20261001`. The fixture allocation is `5776-recovery-rate-t0-20261001-01`. Source preservation does not complete the formal experiment, close the source Draft or [owner #5776](https://github.com/Unjuno/agent-interface/issues/5776), or alter its branch.

## Source presence is distinct from retained result bytes

The exact committed package contains only PLAN.md, audit.py, candidate.py, fixture.json and test_recovery_rate.py. It does not contain a raw ledger, machine audit result, stdout, machine SOURCE_FREEZE/FREEZE manifest, or formal-run receipt. PLAN.md itself contains a source-hash list, a prose host-construction disposition and a prose Docker STOP receipt; those narrative records are retained. No missing outcome artifact was generated for this archive.

PLAN.md and [owner comment 5924979939](https://github.com/Unjuno/agent-interface/issues/5776#issuecomment-5924979939) report a complete 160-episode / 1,280-opportunity host construction, calibration threshold 3.5, gradual held-out warnings 5/20 (0.25 versus the declared 0.75 sensitivity gate), stable-null and load-drift false alarms 0/20 each, and 20 abrupt-breaker episodes with UNKNOWN return endpoints. Their reported method disposition is `FAIL_METHOD`. They also report independent raw-only reconstruction, 6/6 mutation rejections and 3/3 host tests. These are historical source/owner claims; this preservation work did not rerun, independently reproduce or validate them, and the package lacks their committed raw/result bytes.

The recorded formal-resource disposition is `STOP_RESOURCE_COORDINATION_BEFORE_DOCKER`: Docker candidate=0, Docker auditor=0. The historical 04:41 UTC read-only shared OrbStack inventory had four unresolved Created containers and no isolated guest assignment/route. Source code specifying an invocation count of 1 is a planned execution contract, not evidence that a Docker invocation occurred. This archive does not inspect or touch containers, allocate a slot, or retry the experiment.

## Frozen-byte observations

All five materialized byte sequences reproduce their published Git blob IDs. The four embedded PLAN.md SHA-256 claims for fixture.json, candidate.py, audit.py and test_recovery_rate.py exactly match the committed bytes. PLAN.md intentionally omits its own digest; the archival manifest supplies the actual fetched-byte SHA-256 `17d34785ef4d4b6f1eac5e803ce31c7999934f05c2c8ef702899a728d317ad65`. This demonstrates source-byte identity only. There is no committed raw/result digest in this five-file set against which to verify the reported host outcomes.

## Static limitations visible in the retained source

These are read-only source observations, not a fresh scientific result:

- PLAN.md's model description says the statistic uses the last four opportunities. candidate.py's build_raw() and audit.py's reference_episode() compute the median of all known recovery ticks in the episode. This text/code discrepancy is preserved; no source or plan has been repaired.
- test_recovery_rate.py expects the unmutated reconstruction to return `heldout_gradual_sensitivity_gate`. audit.py's mutation_results() treats any nonempty reconstruction-error list as a rejection. Consequently the reported 6/6 rejection count is not, by itself, evidence that each mutation introduces a newly detected integrity error beyond the baseline method-gate failure. No mutation was run here.
- PLAN.md's historical receipt says the analysis-index check was unavailable in its sparse checkout, whereas the later PR body and owner comment report a passing index check after a main refresh. Both chronological claims remain as published; preservation makes no new test-pass claim.

## Distinct allocations and continuing ownership

Merged [PR #5792](https://github.com/Unjuno/agent-interface/pull/5792) added recovery_sentinel_5776_t0_v1 and recovery_sentinel_5776_t0_v2, with different source sets and allocations. Merged [PR #5859](https://github.com/Unjuno/agent-interface/pull/5859) added recovery_sentinel_5776_contrast_t0_20261001. Neither delivers this recovery_rate_5776_t0_v1 five-file package. Their separate Docker results and later integrity qualifications must not be pooled with this host-only source package. In particular, [owner comment 5925078612](https://github.com/Unjuno/agent-interface/issues/5776#issuecomment-5925078612) records the distinct #5792 v2 published-artifact fixture/hash integrity correction from merged PR #5798; this archive does not revalidate that different bundle.

Owner #5776 also records later probe-intervention allocations and corrections, which remain distinct and outside this archive. This is finite authored synthetic-method source preservation and reported host failure/STOP only. No empirical Agent Interface, live-task, predictive-utility, incident-prevalence, safety or production claim follows.
