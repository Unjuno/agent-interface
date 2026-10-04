# First ordinary construction and audit repair

Construction01 used two distinct mini cells with completed-sample cap3, stdin,
full reads and authored8ms returning sleep. Its native candidate ran once in
the owned private Engine; client/container exit0 and source-before/after hashes
match. The original source capped at3 samples with no effect; repair reached
FINISH and exact completion effect after one sample. Original raw and output
files remain in run-01/result; no native candidate was replayed for the repair.

The first data-only audit found `m00:STATS` and then raised IndexError in its
missing-sample control. Its exact code is auditor-first.py; the first endpoint
errors/source hash and observed tool exception are in AUDIT-FIRST-ENDPOINTS.json.
The initial tool exception had no separately instrumented file stderr receipt;
none is backdated. Fresh ordinary RED checks subsequently retained one failure
and two errors, exit1. Public logs are marked derivatives; originals are private
and pinned by RED_PUBLICATION.json.

Fixes guard missing sample records rather than indexing beyond the end and
account for skipped periods on the final scheduled-but-raising budget callback.
The existing stdin updates that accounting before invoking the sample; there
is no completed scorer row for this final attempt. No source/runtime copy, raw,
sample cap, hypothesis gate or formal allocation was changed. The fixed data
oracle reconstructs the same two minis and rejects all10 named private
copied-raw controls. Three ordinary regression methods pass normal and optimized
Python, with actual commands/times/exits/logs retained. The repaired standalone
data-only audit exits0, with method/hypothesis scoped PASS; no formal result is
inferred from construction. Final freeze and source commit follow this repair.
