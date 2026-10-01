# Image notice with operation and release evidence

The primary review notice previously carried local title feedback but omitted
the input and Save outcomes. Primary use therefore needed a separate receipt
file lookup for every task. The notice now includes a labelled receipt
projection: operation/transport status, errors, recovery state, emissions and
release evidence, plus a full receipt path. It does not infer task success.
Capture, guard and wait details remain in the immutable request rather than
being repeated in the notice. An initial refusal remains visible after repair.

## Actual use and source boundary

Live source `73e692492`: WSL Ubuntu, same system Python and Chrome for Testing
paths, persistent route, seed 991288. The primary assistant supplied all points
and all six outcome interpretations. Decision publication, same-process polling
and image rendering were chained within one `functions.exec` call; no helper
model or subagent supplied decisions. Native stdio emitted a JSON notice and
image path; the host's `view_image` rendered the image in that same outer call.
This is not evidence of a refreshed registered MCP server or one lower-level
tool call per task.

Six independent exact submissions, no duplicates/missing tasks, task-4 old-layout
refusal with zero emissions and one fresh-image repair. Eighteen completed
programs released input; tracked children ended 0/1/0, not a full descendant
cleanup proof. The run exited 0. All six normal result reviews used the notice
and image without a separate receipt-file read. Recovery needed one extra read.

After this run, the same projection was added to the repair grounding notice.
That final presentation change was tested with a saved-refusal read-only replay
and unit coverage, not another live GUI run. The replay is labelled explicitly;
the actual run and its longer recovery interval remain unchanged.

## Descriptive comparison, not a speed guarantee

Comparison source is the retained `native-primary-review-01` run (source
`54e719e28`), not a new rerun of old evidence. Both use the same seed/task schedule
and application paths in the same primary conversation. Model identity/config
and the full environment were not independently attested. These are two
sequential construction runs, without randomization or replication.

| Quantity | Earlier separate lookup | Notice + combined host call |
|---|---:|---:|
| Median feedback-to-primary acknowledgement | 23.85 s | 16.93 s |
| Unrepaired action-to-feedback range | 0.635–0.722 s | 0.724–0.817 s |
| Task-4 action-to-feedback, including primary repair | 24.04 s | 39.32 s |

All six rows, including the slower repair, are in `comparison.json`. Review
timing includes host polling, image delivery, conversation/inspection and
decision publication, not pure inference or an observable instant of cognition.
The code change and host orchestration changed together. These observations do
not isolate causation, prove overall speedup, or establish human-like tempo.
Actual model tokens/cost remain unmeasured; the richer notice is not claimed to
reduce text size or tokens.

The 227-file archive retains actual stdout notices/decisions, images, raw
receipts, exact submission history, all timings, cleanup, the labelled repair
replay and local test logs. Local checks passed: 174 protocol + 68 harness =242.
Run `python runtime/results/native-review-notice-01/verify.py` for read-only
hash, image, receipt-projection, review-order, effect and comparison checks.

Scope under #2789: reduce primary receipt lookup roundtrips in the existing
desktop path. Overall acceptance remains `HOLD_INTEGRATION_INCOMPLETE`.
