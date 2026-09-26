# #4220/#22 engineering continuation: incremental temporal notification transport

## Purpose and chronology
One usable, authority-neutral streaming boundary for the already retained three temporal contracts. The old API `policies.evaluate` accepts a whole request; this adapter lets the same monitor instances consume individually framed events. This is engineering verification using retained inputs, NOT a fresh X11 scientific replication, a new temporal theorem, or proof of the global roadmap. No new successor Issue is necessary for this transport implementation. It does not own #2255's degraded-live-evidence allocation.

Intake main: `4a1f3957e91b412a64769199f78f2c4b0102d28b`. GitHub MCP read main, README, CURRENT_GOAL, ROADMAP, recent open/closed Issues and open PRs, first100 branch names, #4220 comments, PR#4224 and #2255/comments. Targeted temporal/chunk and temporal-stream branch searches returned adjacent studies, not this adapter. Coverage is bounded and non-atomic; unpublished work is unknown.

The current connection exposes48 read actions and no GitHub write action; plugin discovery found only the already-installed GitHub provider. Docker and gh executables are absent here. This continuation deliberately uses a LOCAL source/gate freeze for a bounded engineering test; it does not claim public preregistration or meet a requirement for public source commitment. GitHub delivery remains a separate outstanding action, not an experiment result.

## H — testable engineering hypothesis
For each well-formed retained event stream, keeping one instance of each unchanged monitor across all received chunks produces exactly the historical three-contract result at every accepted event. Changing OS read cap among1,7,4096 bytes must not change those outputs. EOF/close cannot advance source time. Truncation, malformed framing, duplicate sequence and foreign identity cause an explicit transport error without changing any previously emitted historical result or granting authority.

## T — fixed verification matrix
84 fresh adapter processes:24 historical native-stream inputs x3 OS read caps =72 equivalence trials;12 explicitly derived invalid-input controls, each at read cap7. The72 trials are repeated transport evaluations of24 old observations, NOT72 new independent X11 observations. No old actor/case/formal runner is invoked. Inputs retain exact epoch/ordinal/server_ms/label values; only their transport envelope changes from one full JSON object to NDJSON open/event/close records.

Normal publication is one parent write sequence to a real OS pipe; the child requests at most the declared read cap and logs every actual received byte chunk. OS reads may coalesce writes; actual read sizes, rather than assumed write boundaries, are retained. stdout/stderr go to private regular files to avoid output-pipe deadlocks. Parent records actual wait status, timestamps, argv and PID. No application, model, keyboard/mouse, XTEST, installation or experimental network operation occurs.

Four exclusively consumed21-process batches, fixed case IDs0..83. Child wait3s, batch12s, outer supervisor16s, outer tool20s. Complete previous outer exit is required before the next batch. Stop on process/source/accounting error, no replacement/exclusion/evaluation rerun or outcome-based tuning. Separate construction:12 unittest methods, all single-byte split positions of one Unicode control, and three excluded pipe processes. Construction is not pooled.

## D — acceptance
PASS_LOCAL_STREAM_TRANSPORT_ENGINEERING only with all84 first records and four observed outer exits; unchanged source/data hashes;216 original event-prefix evaluations match both retained outputs and a separately coded declarative oracle; all72 transports close at real EOF; all12 controls give their frozen typed error and exit2 without a complete-transport claim; no authority/task-success inference; effective raw-evidence corruption controls all reject, change bytes, and produce no auditor exception. Complete discrepancy is FAIL; absent source/raw/exit evidence is HOLD/STOP. This does NOT change either older allocation's formal acceptance.

## C — competing explanations and limits
This verifies an implementation of known byte-stream framing, not a newly discovered OS behavior. Deterministic read caps are directed segmentation conditions, not estimates of natural fragmentation frequency. The old whole-request API was not promised to be a persistent streaming API and is not labelled defective. One trusted sender and one fixed clock/channel epoch are assumed. Local ordinals do not authenticate the producer or detect consistently renumbered omissions. No restart/resume, concurrent writers, network protocol, production integration, model usefulness or latency/token benefit is established.

## U — uncertainty
Counts, bytes and source identities are exact under the retained fixture. Runtime and timestamps are diagnostic, not a benchmark; hardware frequency is not controlled. No population error rate, combined physical standard uncertainty or coverage factor is inferred. The missing old outer execution receipt remains missing; process absence and new audit success cannot recover it. Same-author separate oracle/process is not independent human review.

## Protocol variable/field table
| Symbol/field | Meaning | SI unit | Definition | Range/assumption | Type |
|---|---|---|---|---|---|
| epoch | Channel identity | 1 | Exact caller-supplied UTF-8 string |1..128 encoded bytes; trusted source identity, not authentication|string|
| ordinal | Event order |1|Contiguous local sequence from1|1..128, exact integer, not Boolean|scalar integer|
| server_ms | X-server tick |s, encoded ms|Unchanged recorded32-bit counter|0..4294967295; nondecreasing; no wrap in a stream|scalar integer|
| delta_ms | Source-time allowance |s, encoded ms|Fixed80, inherited from the study|exact integer80|scalar integer|
| read_size | Maximum requested pipe read |1, byte count|CLI cap per os.read|1,7,4096|scalar integer|
| MAX_LINE | Line capacity |1, byte count|Maximum bytes before LF|4096|scalar integer|
| MAX_TOTAL | Stream capacity |1, byte count|Maximum incoming bytes including LF|65536|scalar integer|
| phase | Transport lifecycle |not applicable|NEW/OPEN/CLOSING/CLOSED/ERROR|one process/one channel|enumeration|
| historical_result | Per-contract historical outcome |not applicable|Result at last accepted event|PENDING/SATISFIED/EXPIRED/UNKNOWN as applicable|record of enums|

Dimension check: source deltas compare millisecond counters only; parent nanosecond clocks are used solely for process bracketing. They are never subtracted from server ticks. Read capacities count bytes, not events, elapsed time or model tokens.

## Conditional correctness argument
Initially the framing buffer is empty and no monitor exists. On each non-LF byte, the deterministic state transition appends exactly that byte unless its explicit capacity has been exceeded. On LF, the buffer contains exactly the preceding complete record; UTF-8/JSON decoding happens only then. Its interpretation depends on those record bytes and the preceding state, not the enclosing os.read boundary. Consequently, induction over the input bytes gives the same frame sequence and error position for any segmentation of identical bytes. EOF is a separate finalization event; an unclosed line or missing close is an error rather than a source-time advance.

For a well-formed open, the same three monitor constructors as the historical evaluate() are called once. At the first accepted event their arguments agree. Inductively, if monitor states agree before an event, both call the same unchanged feed method with the same source tick/labels or same event object, so their new states and outputs agree. No state is reset at a read/line boundary. Close does not call feed. This establishes equivalence for well-formed bounded streams under the unchanged monitor semantics. Invalid input is deliberately a stronger transport contract: even after historical SATISFIED, a malformed subsequent message makes transport ERROR while preserving that historical result, not silently validating the whole stream.

ERROR CHECK: this argument assumes exact byte identity, a single source epoch and complete sequence metadata. It does not prove source truth, gap absence, causality, fresh-at-use status or business-task completion.

## Roadmap
Original byte verification/read-only re-audit -> adapter construction -> local source/fixture/gate freeze -> four first-outcome pipe batches -> independent raw oracle/corruption checks -> complete original+new evidence and additive patch -> permitted GitHub publication and existing-PR review -> qualified evidence merge/readback. No remote branch deletion while #4224 depends on it. Global ROADMAP remains open.

## Primary background
POSIX read: https://pubs.opengroup.org/onlinepubs/9799919799/functions/read.html
Python subprocess: https://docs.python.org/3/library/subprocess.html
These document byte-stream read/EOF and actual process wait behavior, not the result of this test.
