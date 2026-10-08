# Recovery review: Issue #4007 exact-value evidence handoff

The 2026-09-22 branch contributes only `REPORT.md` at this path. Its report
describes retrospective publication of an already executed 90-condition
allocation and explicitly says that a report alone is not raw evidence. The
original ZIP, 71-member archive, `PUBLICATION.json`, raw files, and readback
manifest are absent from this branch and were not found in accessible
workspace/temp/download paths. No complete evidence bundle is being claimed
or reconstructed here.

## Reported result and limits

Issue [#4007](https://github.com/Unjuno/agent-interface/issues/4007) and the
recovered report describe `PASS_EXACT_VALUE_SUCCESSOR_SCOPED`: 90/90
candidate/oracle classifications; 9 PASS, 36 FAIL, 45 HOLD; zero candidate
false PASS; raw-audit errors/provenance errors empty; 14/14 raw mutations and
1/1 copied-source mutation rejected; and 13/13 unit tests. The report lists
hashes for the local ZIP, original raw JSON, and full 71-member archive. Those
bytes and `PUBLICATION.json` are not in the recovered branch, so the hashes
and outcomes remain report/Issue-reported, not independently verified from
repository-resident artifacts.

The report keeps the historical local-only preregistration chronology,
previous extraction/inventory incident, and independent-evidence limits
explicit. The experiment uses a stronger authored EXACT_VALUE contract; this
does not establish equal-information superiority, causality, production GUI
safety, or model/task benefit. The distinct #3951 ablation lane is untouched.

## Recovery boundary

`REPORT.md` is retained byte-for-byte as a provenance summary, not as closure
of its own evidence-delivery gate. No formal/native case, GUI action, model
call, or archive reconstruction was executed. Keep #4007 and its parent
follow-ups open; if the exact original archive is recovered later, verify its
member hashes and rerun only the offline audit before claiming complete
publication.
