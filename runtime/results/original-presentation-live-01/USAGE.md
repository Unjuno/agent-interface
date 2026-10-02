# Actual combined primary usage

The corrected actual-source projection contains 13 unique responses, independently
replayed against 39 original source lines from this primary's own session only.

| Counter | Tokens |
| --- | ---: |
| Input | 2,476,070 |
| Cached input, subset of input | 2,459,904 |
| Uncached input | 16,166 |
| Cache-write input | 0 |
| Output | 6,438 |
| Reasoning output, subset of output | 3,676 |
| Total input plus output | 2,482,508 |

The inclusive window starts at keeper launch and ends after explicit close,
owner terminal, first independent app-event/pixel/hash read and fifth same-file
primary image view. It includes primary control, driver authoring and inspection.
Earlier scaffold/build and later verification/accounting/publication are excluded.
Requested source context is gpt-6.1-sol / medium; provider revision and dollar
billing are unavailable. Cached totals represent repeated existing context, not
image-only usage or free work. This is neither a per-call image-token estimate
nor a route/model comparison; no savings or efficiency claim follows.

The first selector matched its own source-writing tool call. Its real usage
projection is retained unchanged as usage-first-self-match.json but is invalid
for the live-case window and excluded from the totals above. The corrected
selector excludes its own generation/execution calls; exact input boundaries
are independently checked in usage-boundary-check.json. A supplementary checker
first read the end output record as call input (KeyError); its failure note is
retained and the corrected checker uses first/last call records. These bookkeeping
repairs did not rerun the live allocation or input. Source replay and selection
validity are separate obligations.

The exact 39 selected source rows are now retained in actual-source-records.jsonl.
Offline replay is available via verify_retained_source.py; it also compares all
five actual tool-output image blocks to the original PNG files. This adds no
responses to the original usage window and changes none of its counters.
