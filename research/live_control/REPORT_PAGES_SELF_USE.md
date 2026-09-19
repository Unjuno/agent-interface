# Actual saved-report inspection with a deliberately omitted display

The assistant read the historical pair 3 B build result through the unchanged
v1 pager at a 4096-byte wire limit. Six distinct pages covered 17,624 source bytes.
The second CLI response was deliberately withheld from model display while retained
by orchestration. The cursor stayed at 3440, and a separate CLI call at that same
cursor returned an identical page. Subsequent pages were individually displayed.
Seven CLI calls, six displayed pages, zero runtime/task-input calls.

The final text showed `build-road` completed with three steps and verified input
release; task scoring remains separate. This is inspection of an existing report,
not a new live task or independent model-performance trial. No image was requested.
The omission was injected after successful CLI transport, not an observed transport
failure. Display flags are orchestration records, not authoritative model receipts.

`audit_report_pages_self_use_v1.py` verifies exact source reconstruction, the retry's
equality, displayed-page sequence, all page wire bounds, and rejection with the second
displayed page missing. Unique wire bytes total 21,056; including the deliberately
omitted response they total 25,152. Envelopes and escaping add overhead; these are
not actual model tokens. Evidence is `results/report-pages-self-use-01`.

Observed usability problem: the first page ends in coordinate `64` and the next
starts with `1`, splitting the original value 641. Other pages split JSON structures.
Exact reconstruction is useful for recovery, but fragments are awkward for judgment.
Keep this primitive as a fallback. Next improve page boundaries to prefer complete
lines within the same exact byte/wire constraints, falling back explicitly for a
single oversized line. Test numbers, escaped strings and Unicode without changing
this measured v1. A line is still not a semantic event or proof of input authority.
Black-image delivery and authoritative receipt/token accounting remain unresolved.
