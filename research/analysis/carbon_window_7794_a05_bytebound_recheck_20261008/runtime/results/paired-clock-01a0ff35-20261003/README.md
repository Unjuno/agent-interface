# Native paired clocks and the post-dispatch wait test

A receipt with integer nanosecond fields can still use a coarse clock. In this
fixed Windows run, nine of twelve `time.sleep(0.020)` calls had a monotonic
receipt difference below 20 ms while the nested `perf_counter_ns` interval was
at least 20 ms. The existing post-dispatch test used the receipt difference to
assert the actual minimum wait and could reject a correctly completed sleep.

The accompanying change affects only
`runtime/cli_v1/test_post_dispatch_capture.py`. It measures the actual sleep
with the standard high-resolution elapsed counter, retains the requested
minimum, and still checks receipt ordering, one exact sleep argument, release
before wait, capture after wait, original retained report bytes, and read-only
lookup. A new regression fixes the receipt clock at a coarse value while an
actual 1 ms sleep runs. The production session, public summary, backend,
authority, thresholds, platform skips, and runtime receipt schema are unchanged.

Python documents the elapsed counter for short-duration measurement and exposes
clock implementation/resolution through `get_clock_info`; integer nanosecond
representation does not establish the underlying resolution.
[Python 3.12 time documentation](https://docs.python.org/3.12/library/time.html).
The implementation names below are observations of this particular bundled
3.12.14 binary, not assertions about every CPython 3.12 distribution.

## Fixed scientific allocation

Allocation `paired-clock-01a0ff35-20261003-A01` was frozen at
2026-10-03 07:06:05.529583 UTC against repository context
`4ada7f511ce451caa4050c78b7fa4b3afe6b6f72`. The prospective claim is
[#57 comment5966617269](https://github.com/Unjuno/agent-interface/issues/57#issuecomment-5966617269).
Exactly one attempt produced all twelve declared rows between
07:06:59.287453 and 07:06:59.536398 UTC; no rows were excluded or repeated.
The unchanged frozen reader ran separately under `-O` against the private
original plan and decided `SUPPORTED_IN_FIXED_RUN`.

| 記号・量 | 日本語の意味 / definition | 単位・範囲 |
| --- | --- | --- |
| r | 要求した待機時間 / requested sleep | 20,000,000 ns in every row |
| m | 同じmonotonic時計の終了値−開始値 / receipt elapsed | ns; observed 15,000,000–31,000,000 |
| p | 同じperf時計の終了値−開始値 / nested elapsed | ns; observed 20,175,300–20,587,300 |
| paired witness | `m < r <= p` を満たす行 | rows 0,1,3,4,6,7,9,10,11 |
| monotonic resolution | APIが報告した時計分解能 | 0.015625 s; `GetTickCount64()` |
| perf resolution | APIが報告した時計分解能 | 0.0000001 s; `QueryPerformanceCounter()` |

The subtraction uses only two readings of the same clock. The perf interval is
nested inside the monotonic interval by instrumentation order; absolute epochs
are never subtracted across APIs. Conversion to ms divides ns by 1,000,000.
No perf interval was below the fixed 20 ms criterion. A short-perf row would
have been retained as `COUNTEREVIDENCE_SHORT_PERF`; no favorable-phase search or
threshold relaxation was allowed.

The host snapshot is Windows 11 Home x64, Intel i7-12700H, 14 cores/20 logical
processors, reported 2300 MHz, 3% snapshot load, 17,528,540 KiB free RAM and
57,217,101,824 bytes free disk. It is not a reservation or proof of load during
the burst. Twelve sequential observations on one host are not independent
failure-rate trials. API agreement does not calibrate physical elapsed time,
prove every earlier MCP failure's cause, establish GUI settling/task completion,
or measure product speed, model cost or general reliability.

## Ordinary repair and integration outcomes

All ordinary stages are separate from A01 and consumed historical allocations.
Exact commands, source inventories, UTC boundaries, first streams and exit
codes are retained. The environment is native Windows Python 3.12.14,
MCP 1.30.0, Pillow 10.2.0, numpy 1.26.4, pydantic 2.13.4 and anyio 4.14.2.
The SDK and PNG fixtures use an inert input backend; no live GUI/native input,
GPU, Engine, WSLc, new worker or model call was allocated.

| Stage | Actual result |
| --- | --- |
| First coarse-clock regression | 1 method, exit1: the original `0 >= 1,000,000` receipt-duration assertion fails |
| Test observer repair | 21 methods, exit0: nine post-dispatch and twelve public-summary methods |
| First actual shared native entry | protocol413 methods /2 failures /30 error events /7 skips; then runner exit1 on cp932 console encoding; harness not run |
| Shared native entry with UTF-8 stdio | protocol413 /2 failures /30 error events /7 skips; harness205 /1 failure /39 error events; entry exit1, `FAIL` |
| Public retained-data arithmetic | exit0 under `-O`; exact twelve rows and original audit agree; six semantic controls behave as declared |

The actual common entry is `runtime/integration_checks/native.py`, unmodified.
The second invocation only sets `PYTHONIOENCODING=utf-8`; the first attempt and
its complete protocol logs remain. It is an ordinary repair of the observed
logging failure, not an A01 retry. Both formerly failing 20 ms post-dispatch
methods and the new coarse-clock case pass in the common entry. Remaining logs
include POSIX owner-lifetime/O_DIRECTORY failures, two relay failures, and the
X11 archive import assertion. Their exact headers/streams remain in `RESULT.json`
and `native-utf8-after-repair/`; none is removed, platform-skipped, counted as a
pass, or repaired by this proposal. Error counts include subtest events, so
passing method counts are not obtained by subtraction. No hosted/Linux/all-CI
pass is claimed. The distinct runtime shutdown repair in PR6947 is not included
in this test-only source tree.

`SOURCE.json` distinguishes exact executed working-copy bytes from Git LF
images and verifies identical ASTs including source locations. Each ordinary
receipt retains all 1731 checkout Python source hashes. The complete 484-path
Git metadata comparison to observed main `9c0692dabbfc7fc2fa5bd111b6de4baee578800d`
changes only `research/integration` and `research/doom`; the chosen runtime,
workflow and governing-document scope remains equal. This is an author source
observation, not a current combined-tree approval or a future-base certificate.

## Publication and independent data reading

Original raw SHA256 is
`7774dc4120b655ee476c8ab4a5c0fef8c1ab43d98ef7eb4bb9c92de7ce87adb5`.
The private frozen PLAN SHA256 is
`30afb8c16b1ca629770556c289b93a613c8dfeea705b64e295123df4e944b3dc`.
Private originals were preserved before a path-only public projection. Sixteen
of the original 62 packet files replace the private Windows home prefix with
`C:\Users\WORKER`. `PUBLICATION.json` maps every original/public byte length and
SHA256. Original hash declarations in receipts bind original bytes, so a public
stream is joined through that map rather than silently relabeling the hash.

The frozen probe/reader, START, twelve raw rows, END and original AUDIT are
byte-identical. The public PLAN differs only in private paths. Consequently
the preserved original reader is **not claimed to run against that redacted
PLAN**. The separately named `public_read_rows.py.txt` was written after the
result: it verifies the 62 public projections, the original PLAN/START join,
frozen sources and independent arithmetic, then compares the original audit.
It does not import or execute the probe. Its six controls deliberately lift
outer byte checks: boolean row ID, duplicate ID, missing row, backwards perf
clock and a future freeze are rejected; a valid 19 ms perf counterexample is
retained as `COUNTEREVIDENCE_SHORT_PERF`. This is local arithmetic qualification,
not nonauthor agreement, execution authentication or prospective evidence.

The first public-audit parent failed before creating a child because its
relative executable did not resolve from the parent's cwd. Its original
partial receipt and operational account are retained. Invoking the unchanged
wrapper from the checkout then completed exit0; no scientific producer ran.

For a new **data-only** reviewer output, from a checkout with a Python
interpreter, use a fresh report path outside the package:

```text
python -B -O runtime/results/paired-clock-01a0ff35-20261003/public_read_rows.py.txt --package runtime/results/paired-clock-01a0ff35-20261003 --report /fresh/reviewer-report.json
```

Do not re-execute `probe.py.txt`, `prepare.py.txt` or `run.py.txt`: A01 is consumed.
All archived executable source is inert `.txt`, and no test/entry/workflow
imports this archive. `SHA256SUMS` covers all public packet files except itself.
The disposition is **RETAIN bounded timing evidence and the passing scoped
test repair; shared native integration remains FAIL**. A main application still
requires actual fixed nonauthor content agreement, current-tree applicability,
live GitHub conditions and one identified expected-old history-preserving
sender. No main transmission or whole-goal completion is claimed here.
