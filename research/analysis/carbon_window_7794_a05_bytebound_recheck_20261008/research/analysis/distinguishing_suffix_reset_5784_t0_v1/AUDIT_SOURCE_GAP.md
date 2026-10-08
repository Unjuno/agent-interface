# Formal auditor source retention gap

The formal allocation's `FREEZE.json` records the pre-run auditor SHA-256 as
`1b16689bd98dca7771b60671b9c20febf1712dd085062ed5f0b2a1ac981daa58`.
After the formal auditor stopped, `audit.py` was edited for a separate,
non-promotional diagnostic against the immutable raw. That edit was not a
formal rerun and did not change `out/formal.jsonl`.

The exact pre-edit auditor bytes are not currently recoverable in this scratch
folder. The published `audit_diagnostic.py` is the post-STOP diagnostic source;
it must not be mistaken for the auditor whose hash appears in the freeze.
Therefore the formal source bundle is incomplete and this PR must remain Draft
and unmerged until the missing exact source is recovered or the archival record
is otherwise explicitly qualified without pretending to reproduce it.

Scientific disposition remains `NOT_EVALUATED`. No PASS/FAIL reset-method claim
is supported. The immutable candidate raw SHA-256 is
`f2331d75add8cb11245b64df1e84fb28d5f5cd1cd99758c79122f02f350e7dc2`.
