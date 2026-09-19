# Compact report index v1 — offline prototype, not action authority

Full paged review of one live Inkscape result needed six extra calls. This prototype
indexes an original caller report by source digest, event paths/counts, full terminal
records, selected image reference, caller state/reason, and attention paths. Routine
payloads remain in the original file and can be inspected through the pager.
It is intentionally lossy as a display, unlike the reversible report view.

The name `decision_receipt_v1.py` does not imply a runtime or model acknowledgement.
Output explicitly says it is an index, not full review, schema validation or input
approval. Task success remains unknown even when a program terminal is completed.
`program_sent` is labeled as a possible write attempt, not admission. Image references
are historical; this tool does not capture or display pixels.

Noncompleted/error/unverified-release terminals, unresolved caller state, reply
prefix/status problems, unknown event names, unknown top-level routine-event fields,
inexact images, focus mismatches, and nonquiet settle results surface as attention
paths. All terminal records remain visible. All exchange-event paths are indexed.
These checks are deliberately incomplete: nested schema extensions and semantic
contradictions can escape attention. No attention is not evidence of authorization,
correct attribution, complete evidence, or successful task completion.

Offline recorded cases:

| Case | Original pretty report bytes | Serialized index bytes |
| --- | ---: | ---: |
| Successful live Inkscape move | 54,994 | 3,185 |
| Recorded focus interruption | 19,157 | 2,505 |
| Historical clock / unresolved caller | 1,769 | 1,020 |

The original contains duplicate fields and whitespace, so these ratios are not
fair compression comparisons with the already reversible compact view. No model
token, latency, accuracy or live benefit is inferred from byte counts. Four injected
cases surface unknown events, unknown fields, capture error and focus mismatch.
The probe checks path coverage and source digest. It does not prove full validation.

Run `python3 research/live_control/probe_decision_receipt_v1.py`; evidence is
`results/decision-receipt-01/report.json`. CLI accepts an original report path, reads
at most 8 MiB + 1, and does not contact the runtime. Output is not hard size-bounded;
many attention items or terminal records may still need paging.

Before live use, strengthen the interpretation contract: contradictory top-level
and exchange status, stale own-command identity, nested exceptional fields and
missing final terminal must never be mistaken for a resolved current program.
Either validate these explicitly or require the exact affected evidence to be read.
Retain this measured prototype and its limitations. No default live integration yet.
