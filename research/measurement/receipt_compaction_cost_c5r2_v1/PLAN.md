# Receipt compaction cost — #4395 / #3544

Base: `4c701cc51b06296268ad8d9ae3eff1dd6f2d379d`.
This is a current-function microbenchmark, not a model/GUI/transport experiment.
No production code or default is changed. Preserve all earlier allocations.

## H / T / D / C / U

H: reference compaction can trade extra processing for fewer JSON bytes. The
existing smaller-receipt fallback must preserve lossless reconstruction, raw
input identity, partial outcomes and release uncertainty. It does not minimize
end-to-end latency merely because it minimizes one serialization's size.

T: six generated no-image JSON reports, three existing review_bytes modes
(plain, compact, compact+report_refs), two warmup triplets and21 measured
triplets per condition. Order cycles plain/compact/report_refs,
compact/report_refs/plain, report_refs/plain/compact continuously, including
warmups. Each condition has one fresh source process and69 calls;378 measured
and36 excluded warmup calls overall. One worker per condition, no retries,
replacement, sample exclusions or result-driven source/gate changes.

| Index | Condition | Shape |
|---|---|---|
|0|minimal|Synthetic completed dispatch, no extra detail|
|1|detail_256|Synthetic failed dispatch and256 ASCII detail bytes|
|2|detail_8192|Same with8192 detail bytes|
|3|repeat_8|One512-byte critical event copied into8 diagnostic positions|
|4|repeat_64|Same with64 diagnostic positions|
|5|unique_64|64 distinct critical events;64 nonmatching diagnostic objects|

These are development-known synthetic inputs, not retained live task outcomes.
Non-minimal cases retain a failed release followed by a successful release,
recovery_required=true and failed-operation effect unknown. Their keys and
statuses are test data, not actual input, live releases or task success.
Reference-shaped literals and Boolean/integer distinctions must remain exact.

Producer timing includes complete unchanged review_bytes execution plus
canonical JSON envelope serialization (sorted keys, compact separators,
allow_nan=false, default ensure_ascii=true). It excludes imports, input
creation, file writes and verification. Consumer timing includes parsing that
wire and the existing expand_receipt API, which deep-copies even a v1 view.
That consumer is a declared normalization boundary, not an observed model host.
Retain monotonic/process-CPU endpoints in integer nanoseconds and every output
hash. Keep all first output strings and exact inputs. No images are decoded.

All six upstream implementation files must match main Git objects; two empty
package initializers isolate the unchanged functions without the dispatch CLI
initializer. No function slicing, backend stub or monkeypatch is used. This
exercises public presentation functions, not the full CLI, MCP, backend or
provider path. Source/import identities and inputs are fixed in FREEZE.json.
One allowed logical CPU is selected before measurement; actual hardware/kernel,
interpreter, clocks, cgroup data and frequency snapshots are in ENVIRONMENT.json.
Frequency, neighboring load and physical-core exclusivity are not controlled.

D: PASS_RECEIPT_COMPACTION_COST_CHARACTERIZATION requires six complete workers
with observed exit0, all414 calls and exact frozen sources/inputs, exact
independent expansion to the plain view, identical non-receipt outcomes,
nonincreasing selected canonical receipt bytes, stable output hashes, and10
EFFECTIVE copied-evidence controls rejected by a raw-only separate auditor.
Complete fidelity mismatch is FAIL; missing evidence is HOLD/STOP. Scientific
and process-status evidence are not inferred from one another. No numeric
speedup is required or promised. Audit-code independence is not human review.

C: output serialization is fixed and uncompressed. A real host may serialize,
compress, parse or present differently. Received raw history remains in the
view, so event references cannot remove every duplicate. Content/reference
shape changes which existing format wins. JSON byte counts are not tokens.

U: real receipt distribution, image payloads, model interpretation, actual
transport bandwidth/compression/queueing, cold starts, task effects, memory,
concurrency, energy and end-to-end latency remain unmeasured. Technical
repetitions yield descriptive medians/ranges, not calibrated uncertainty or
population reliability. Combined standard uncertainty and coverage factor are
not estimated.

## Conditional transfer model and units

| Quantity | Meaning | Unit | Definition and scope | Type |
|---|---|---|---|---|
|saved_bytes|Reduced encoded envelope length|byte (8 bits; non-SI)|Plain minus chosen output; nonnegative for eligible crossover|Integer scalar|
|added_seconds|Additional producer-plus-consumer wall time|s|Median paired difference, nanoseconds divided by1e9|Real scalar; may be nonpositive|
|crossover_rate|Conditional effective transfer rate|byte/s|saved_bytes divided by positive added_seconds|Positive real scalar only when both terms positive|

The derivation is direct: extra processing is offset when transfer of the saved
bytes would take at least that extra time. Divide saved bytes by the extra
seconds to obtain the crossover effective throughput. Unit check: byte divided
by second is byte/s. This assumes additive processing and uncompressed serial
transfer, no overlap and identical unmeasured stages. It is not a measured link
rate or a route recommendation. Report missing/inapplicable crossover as null.

## Execution and delivery

Before measurement: public exact source/gate readback. Then run, once each:
`python -S -B run.py 0 formal` through `python -S -B run.py 5 formal`.
Each wrapper observes its worker's actual OS exit and bounds it to20 seconds;
each surrounding container invocation has a30-second bound. Stop at the first
incomplete/nonzero worker. No detached/background service is created.
Then run `python -S -B audit.py formal` and `python -S -B controls.py formal`.
Retain source, inputs, all raw outputs/clocks, process records, construction
record and first audit. Publish losslessly in the owned namespace, verify Git
objects/readback, review exact-head CI before qualified evidence merge. Keep
#3544/#57/#2789/global ROADMAP open. Delete only a supported dependency-safe
owned ref; do not clean other workers' branches.
