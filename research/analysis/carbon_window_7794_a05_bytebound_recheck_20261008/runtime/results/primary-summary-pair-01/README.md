# Primary full/summary pair on the public runtime

The primary used the existing public `detail: 'summary'` API in a fresh browser
session and completed the same task as a fresh full-receipt session. Both entered
`t1001035-4`, reviewed the entered value, saved once, and reviewed the actual
`AI INTEGRATED SAVED` image. This adds caller guidance and retained usage evidence;
it introduces no compressor, runtime behavior, default change or sensor.

## Conditions and correctness

Source/build: main `8ee4ff891a54827b3df3df297cdb849e2aea428e`, portable runtime
335,354 bytes, Windows primary relay host, Ubuntu WSL 3.0.1 package with WSL 2
distribution architecture, private Xvfb 1280×800, Chromium 145.0.7632.6,
`persistent-x11`. Local Codex turn context labels the primary `gpt-6.1-sol`,
medium effort. This is a previously encountered task family with fresh seed
1001035; it is not held out. Full was run first, summary second.

Both arms used `compact: true, report_refs: true`; only `detail` changed. The
baseline is full v3 with one raw report reference, not the older duplicated v1.
Per-allocation URL port, program identity and absolute deadline differ. The
normalized operation arguments are identical. Navigation/save observations cover
1280×800; entry uses [430,470,400,210]. Requested fixed waits total 400/200/100 ms.
The two entry PNGs are byte-identical. Navigation/save PNGs differ because their
URLs use different allocated ports; representation does not alter any PNG.

Each arm: 11 MCP calls, consisting of five clock reads, one initial observation,
three executed input programs, one expired control, and one close. Four images,
four primary review records, zero extra observations, zero full retrievals, zero
input replay, zero recovery calls. Independent append-only submission history
contains task-4 exactly once. The fixture's six-task aggregate remains false:
tasks 1/2/3/5/6 were allocated but were not requested in this comparison.

All executed programs released tracked input with empty verified key/button
state. Both expired focus/observe/release-only controls returned LEASE_EXPIRED
and retained the full receipt; cumulative backend emissions stayed 98. Both
transports and the original fixture process handles exited 0. Each fixture's
recorded child cleanup codes were [0,1,0]; they are retained unchanged rather
than reported as all clean exits.

## Same-report text size and live component timing

| Summary arm report | Full text UTF-8 bytes | Delivered summary bytes |
| --- | ---: | ---: |
| Navigate | 5,651 | 4,045 |
| Enter | 5,593 | 4,064 |
| Save | 5,252 | 4,029 |
| Total | 16,496 | 12,138 |

This is 26.42% less text for the same three reports, using the transport's JSON
serialization. Raw data and images remain available. The separate full arm
actually delivered 16,469 bytes; its per-session path lengths differ. This is a
text-byte result, not a token or dollar saving. The archived read-only analyzer
reconstructs full presentation and checks exact delivered full/summary rendering
against the shipped implementation, without GUI input.

| Dispatch | Full host send → reply ms | Summary host send → reply ms |
| --- | ---: | ---: |
| Navigate | 514.712 | 505.862 |
| Enter | 258.255 | 254.365 |
| Save | 172.372 | 178.160 |

These include runtime waits, capture, presentation and transport. They are one
fixed-order pair, not evidence that summary speeds up the task. Capture end
occurs about 432/209/112 ms after execution start in full and 431/206/108 ms in
summary; application readiness was established from the viewed image, not from
capture or dispatch completion.

Host send → caller review record was 13.953/14.125/39.016 seconds in full and
14.987/13.507/416.285 seconds in summary. The last summary record was delayed
across context compaction and the user's WSL environment request; the saved
image had already been delivered. Review records are caller declarations, not
timestamps of first semantic recognition. The gap remains in raw evidence and
must not be relabeled as model perception latency, omitted, or rerun to create a
better-looking task time. Human-comparable live tempo remains unproven.

## Actual primary model usage

The projection retains local usage counters and matching tool request/output
call IDs, timestamps, input hashes and observed turn context. Private
conversation content is excluded. Core request-authoring records:

| Arm / next action | Whole-context input tokens | Cached input tokens |
| --- | ---: | ---: |
| Full / navigate | 227,444 | 223,744 |
| Full / enter | 230,606 | 227,072 |
| Full / save | 232,727 | 230,272 |
| Summary / navigate | 239,619 | 237,568 |
| Summary / enter | 242,246 | 239,488 |
| Summary / save | 243,881 | 241,920 |

These are actual counters, not a tokenizer estimate. A usage record between a
request and its output measures the response authoring that request; it cannot
contain that tool's new receipt/image. First subsequent usage records are also
retained to expose chronology, but include the entire growing conversation and
may cross compaction. Request/output association is by call ID; usage association
is chronological, not a provider-attested per-tool foreign key. Model/effort are
the locally observed turn labels, not an independent per-response attestation.

The full arm's outputs remain in the summary arm's context; cache and context
growth confound arm comparisons. There is no isolated receipt/image token cost,
causal token-saving percentage, actual billing record or dollar result.
`dollars: null` means unmeasured. More compact tool text is useful, but these
records do not demonstrate lower whole-task model consumption.

## Integration decision and limits

Use the shipped explicit partial summary when deciding the next action from the
current image, execution outcome, input release and session state. Read the
retained full result when a decision needs omitted operation/wait/provenance
details. It is historical evidence and does not refresh the image. The summary
keeps complete capture/release/activation records and source digest; it grants
no authority or semantic success. Failures and unsupported shapes stay full.

Issue #5329's task-conditioned sufficiency proposal motivates declaring the
consumer decision, but its four-packet toy audit does not validate a new product
sufficiency schema or general safe compression. This integration reuses the
existing conservative public gate. General multimodal compression, unfamiliar
task coverage, matched latency, isolated model cost and human tempo need further
evidence.

## Retention and verification

`raw.tar.gz` and `manifest.json` retain 127 files: plan, source caller, portable
build and hashes, two fixture setups, requests/replies, exact PNGs, raw reports,
reviews, scorer histories, actual cleanup codes, component analysis and model
usage projection. No conversation log is archived.

From repository root:

```sh
python3 -O runtime/results/primary-summary-pair-01/verify.py
```

The standalone read-only verifier checks archive/member identities, scoring,
operation parity, source/PNG/review identities, selected preserved records,
call accounting, failure fallback, component timings and six core usage records.
It does not replay the task, independently interpret pixels, validate every
possible summary contract or prove performance. The archived analyzer depends
on the production presentation code and original owned image paths; it is an
additional local rendering check, not the standalone archive verifier.
