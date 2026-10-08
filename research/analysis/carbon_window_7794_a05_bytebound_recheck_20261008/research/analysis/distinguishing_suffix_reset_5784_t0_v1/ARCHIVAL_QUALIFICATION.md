# Archival qualification: incomplete formal auditor record

The original allocation remains `STOP_AUDITOR_SOURCE_DEFECT` with scientific
disposition `NOT_EVALUATED`. Candidate invocation=1, exit=0; independently
invoked formal auditor=1, exit=1; formal retries=0. The immutable synthetic raw
SHA-256 is `f2331d75add8cb11245b64df1e84fb28d5f5cd1cd99758c79122f02f350e7dc2`.

The formal pre-run `audit.py` bytes are absent. Only their frozen digest,
`1b16689bd98dca7771b60671b9c20febf1712dd085062ed5f0b2a1ac981daa58`, remains in
`FREEZE.json`. The published `audit_diagnostic.py` is a different, post-STOP
diagnostic source with SHA-256
`8fc5bdbffaee2beca040121f6933d7fd9c77c1c8ef456a4849b9b18251564f0f`.
It must never be substituted for, executed as, or described as the formal
auditor. `out/audit.json` is the later diagnostic output (`rows=0`,
`FAIL_METHOD_OR_EVIDENCE`), not the failed formal auditor's output and not a
scientific disposition. The formal auditor stopped before assessment.

The planned standalone report and execution transcript are not present among
the original nine published files; the STOP narrative records reported
invocations and exit codes, not a recovered complete transcript. No missing
record is reconstructed, and this is not a reproducible method result.

All eight historical checksum entries and all nine Git blob identities match
at original head `2f61cc3d4c23712205a1037320c560231c5b404c`. This verifies the
available published record only; it does not cure the absent formal source.

The frozen plan did not model controller/planner context, prompt ancestry,
tool/session caches, or scorer state. It supports no matched-agent-start
inference. The six rows are synthetic and do not establish GUI reset fidelity.
[Issue #5784](https://github.com/Unjuno/agent-interface/issues/5784) remains
open. No frozen plan/source/result is changed, no allocation is retried, and
no experiment or diagnostic is authorized by preservation-only integration.

The original `AUDIT_SOURCE_GAP.md` explicitly permits an archival record to be
otherwise qualified without pretending to reproduce it. This addendum qualifies only that preservation route through ordinary review
and CI gates; it does not waive the
missing-source restriction for verified research. Original placeholder and
later publication commits remain in branch history.

`ARCHIVAL_INVENTORY.json` records all nine original published files, including
the historical checksum list, as a current custody inventory. It does not
replace the freeze, recover the missing auditor or transcript, or supply a
backdated report. This archival integration does not close Issue #5784.
