# Host time partition on retained primary use

The read-only summarizer now partitions a complete first-send-to-last-reply span into request-outstanding intervals, presentation-callback intervals and other host intervals. This exposes where instrumented time sits without labelling uninstrumented intervals as model reasoning or application waiting.

| Retained session | Span ms | Request outstanding ms | Presentation callbacks ms | Other host intervals ms |
|---|---:|---:|---:|---:|
| Inkscape numeric | 57702.8171 | 2426.8795 | 29.8893 | 55246.0483 |
| Inkscape drag | 75249.2028 | 2246.3534 | 20.2416 | 72982.6078 |
| Calc full | 86185.1161 | 2681.3341 | 37.1091 | 83466.6729 |
| Calc reviewed references | 85659.7700 | 2304.1204 | 20.0541 | 83335.5955 |

These are existing sessions, not four new samples or a causal comparison. Other intervals include primary/caller review, tool orchestration, logging and gaps. Their exact causes are not identified. Request intervals include transport, server execution and persistence. Callback completion is not model ingestion. This does not measure first useful feedback, exact semantic completion, actual provider tokens/cost, human-tempo equivalence or savings.

The observed request share is small in these sessions. This motivates examining end-to-end handoffs rather than assuming that shortening backend waits dominates total elapsed time. It does not justify removing verification boundaries or reducing delays without fresh correctness evidence.

Final presentation/review/close after the last reply is outside the named span. Repeated presentations count separately; partial/empty timelines return null. Tests exercise refusal-ID reuse, repeated presentation, final-presentation exclusion and incomplete evidence. All14 timing tests and the full native protocol/harness checks pass. Raw old evidence is unchanged; new summaries are separate.

Run `python3 -B runtime/results/host-time-partition-01/verify.py` to replay the archived summarizer on four retained host records and compare exact summaries and arithmetic. No GUI/model call or input is executed.
