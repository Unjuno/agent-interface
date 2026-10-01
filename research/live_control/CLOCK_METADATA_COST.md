# Cost of clock metadata and a lossless batch candidate

The timing identity prototype attaches a full clock-domain ID to each raw event.
Before expanding it, probe_clock_metadata_cost.py compares the same 52 recorded
events with and without only that field. Strict equality checks confirm that
other event values are unchanged. Both variants use the same JSON settings.

The newline-delimited payload grows from 35124 to 39648 bytes: +4524 bytes,
or 12.880%. This is raw event serialization, not delivered model context.

Sixteen paired rounds alternate variant order, each repeating the event list
300 times. Median local CPU times per record are:

| Operation | Without clock ID | With clock ID |
|---|---:|---:|
| JSON encode + UTF-8/newline | 4518 ns | 4805 ns |
| JSON decode | 4741 ns | 5012 ns |

Median within-pair CPU deltas are +184 ns for encode and +389 ns for decode.
Those are medians of paired differences, not differences of the marginal medians.
Raw samples and order are retained. Clock descriptor reads, measured warm 100
times, have a median wall duration of 29461 ns and maximum 398267 ns. No statistical
significance, live critical-path effect or model-latency impact is inferred.
Disk flush, delivery projection, frame capture and scheduling under load are not
included. These measurements do not justify a native-language rewrite.

The byte increase motivates an offline representation candidate, clock_batch.py.
For records sharing one explicit domain, it stores that domain once in an outer
batch and reconstructs every record's clock_domain_id on decode. Mixed domains,
missing clock fields and ambiguous duplicate fields are rejected. Explicit null
clock identity remains null; it is never inferred. Source and decoded mutations
do not affect each other. No authority or clock validation is supplied by this
codec; it only preserves existing labels.

The same 52 records round-trip exactly. Using identical JSON-array/object encoder
settings, the original array is 39700 bytes and the packed representation is
35304 bytes: 4396 bytes (11.073%) less. This comparison uses array framing, so its
denominator differs from the newline-delimited measurement above. Empty and
unknown-clock cases round-trip, and four malformed controls reject. Per-event
ordering is preserved.

This codec is not wired into live transport. Its copying/packing CPU cost and
behavior across independently read socket batches are not measured. Any future
integration must make each batch self-describing and preserve gap/interrupt
semantics. Model input tokens, actual cost and end-to-end improvement remain
unmeasured; byte savings are not token savings. Existing measured streams remain
unchanged. Next evaluate the actual delivered batches and codec overhead before
deciding whether to adopt it.

Evidence: results/clock-metadata-cost-01 and results/clock-batch-01, with input
and source hashes. This is a narrow cost audit supporting Issue #46, not completion
of its full timing envelope or cross-domain benchmark requirements.
