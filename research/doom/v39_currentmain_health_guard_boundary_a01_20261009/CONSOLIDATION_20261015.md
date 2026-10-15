# Historical health-boundary evidence consolidation

The original [PR #8801](https://github.com/Unjuno/agent-interface/pull/8801)
and [PR #8814](https://github.com/Unjuno/agent-interface/pull/8814) carry the
same candidate, frozen raw and original audit. #8801 adds the final-admission
mutation follow-up; #8814 adds a source revalidation at its then-current main.
Both additions are retained here. This adopts the evidence package onto current
main without importing unrelated changes from the old base histories.

“Current main” in the original files refers to their named 2026-10-08 sources.
The original 20-file runtime closure matches frozen commit
`a6343bb76e4dc0a4afa32a29c8a485a617faeff8`; this does not mean it matches today's
controller. The synthetic candidate is still one invocation, with no rerun or
new allocation. Its health 89/88/87 boundary and 13-check audit are historical
software-composition evidence, not physical release, live recovery or task
success.

The original checksum list predates #8801's test extension. Nineteen listed
artifacts remain byte-identical; its original `test_audit.py` is preserved at
`history/test_audit_initial.py.txt`. The exact #8801 follow-up test is also
preserved at `history/test_audit_8801_followup.py.txt`. The checksum list is
unchanged; the publication receipt records this explicit path mapping.

On current main, the old test imported the unrelated parent `audit.py`; after
isolating that import, it failed because it compared saved raw against the
changed current controller. The maintained test now loads this package's auditor
explicitly and hashes the actual Git blob at the frozen source commit. It also
rejects an incorrect source hash. This audits retained evidence; it does not run
the historical candidate or claim current controller behavior.

Run the six retained-result/mutation tests from the repository root:

```sh
python -B -m unittest discover -s research/doom/v39_currentmain_health_guard_boundary_a01_20261009 -p test_audit.py
python -O -B -m unittest discover -s research/doom/v39_currentmain_health_guard_boundary_a01_20261009 -p test_audit.py
```

The frozen Git commit must be present locally. Original `run_once.sh` and
`audit.py` remain historical tools with their original source checks; this
consolidation does not authorize re-running the candidate or relaxing those
checks.
