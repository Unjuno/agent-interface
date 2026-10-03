# App-server late/unowned response lifetime — ordinary A01

Current client can return a response that arrived before its request and retain
responses whose requests have already timed out. This archive preserves one new
ten-cell CPU construction against exact current client and a private pending-ID
counterfactual. No production client or registered test/runner is changed.

Source context10fba1d3c9aa0a6fbf39983cdcda099a10df497c, same6194B/SHA
6032c0dd1d7441977afca790d08d1f1012e8f18171691249456fcfe90097617e on
preexecution actualmain a878df7886c5901f86806aed5a4696c81457c9e7.
Comparator SHA8a1b53db17fb12ef5c379eeec2470f774456e010f2e89e9671c6f25ad94134eb:
pending set initialized before reader; allocated ID registered under condition;
received frame always journaled, cached only while pending; request finally
retires ID and cached reply. Other13 method ASTs remain identical.

| Cell | Current retained cache entries / compact bytes | Pending comparator entries / bytes | Journal rows in each arm |
|---|---:|---:|---:|
| Healthy only | 0 / 2 | 0 / 2 | 3 |
| 1 expired + duplicate/orphan | 3 / 12702 | 0 / 2 | 7 |
| 7 expired + duplicate/orphan | 9 / 38040 | 0 / 2 | 19 |
| 23 expired + duplicate/orphan | 25 / 105653 | 0 / 2 | 51 |
| Pre-request id1 + fresh-late id1 | 1 / 4242 | 0 / 2 | 6 |

Future case: baseline sends a new study/held-fresh request but immediately
returns exact unowned-before-invocation result already in cache. Comparator
returns TimeoutError/no result; its fresh reply was deliberately held, then
released after retirement. This is truthful refusal, not successful completion
of the first requested effect. Both arms then complete distinct healthy id2.
All ten healthy rich4097-character result blobs, full2053-character request
inputs, Japanese/accented meaning, notices and all172 sent/received journal
rows agree with literal saved-data oracle. No payload truncation occurs.

Frozen10:37:52.524050UTC /25 pins, freeze SHA
ed6751381946d0a6d0bf4fece075ca2ede6f8664d523fd34e3c6359c03e93625.
Driver21500 runs10:37:58.067589–.176788UTC, exit0/stderr0; one fixture/reader
at a time, native peers0. Every reader/journal and driver-closed fake stream
terminal, terminatecalls0. Saved-only separately implemented same-author
oracle32908 runs10:38:06.450366–.531962UTC, exit0/stderr0: ten literal joins
and12 effective copied-data corruptions refused. It imports neither subject
nor collector. This is implementation independence, not a nonauthor review.

First intake CP932/UTF8 Git decoding failure and first freezer's root-only
document-path StopIteration are retained. Both precede any subject execution;
only intake decoding / freeze_v2 exact canonical document paths were repaired.
No scientific cell/oracle failure, producer/formal replay, criteria relaxation
or source alteration after execution is hidden. Original failed tools lacked
separately captured outer PID/UTC; normalized complete tool errors are retained.

## Scope and custody

Actual complete Python source constructor/request/reader/notification methods
ran on Windows11/CPython3.12.14 with Queue-backed process_factory substitutions
and own actual UTF8 journal files. Valid exact positive integer response IDs
only. Timeout0 is a deterministic protocol branch, not measured timeout
performance. Cache-byte numbers are compact serialized payload bytes, not RSS,
heap size or resource/latency savings. No real Popen, app-server/model/provider,
game, GUI, input, physical release, WSLc, VM/GPU or end-to-end efficiency proof.
Pending comparison does not establish Boolean-ID protection, server authenticity,
premature replies while an ID is active, hard total time/resource bounds or
runtime eligibility/adoption. Boolean222f, send/compatibility5884, codec0b3d,
EOFd447, readerclosebe6f/b04b and journal4d74 retain their source ownership.

SPEC/INPUT/collector/oracle/source and preexecution images remain frozen.
PUBLIC_IMAGE_MAP explicitly joins private and public complete images; only
filesystem spellings in metadata are projected. Journals/results/input/source
bytes remain exact. Python snapshots end .py.txt and are inert. SHA256SUMS
contains every package image except itself (no stale/self manifest target).
Freeze dependency paths are provenance, not a public execution certificate;
primary executable/library SHA pins remain preserved, binaries are not bundled.

Read INPUT.json, SPEC.md, SAVED_AUDIT.json, a01/RAW+journals and both PROCESS
receipts together. A separately allocated saved-data-only audit may copy
saved_oracle.py.txt to saved_oracle.py beside INPUT/a01; it executes no subject.
Old consumed/first native/formal experiments must not be replayed.

Parent #59/#57; claim5968227616, actual worker
01a0ff33-df63-7d60-871f-a7ecd2649d07 / FINAL-v5. N/commondeadline unknown and
unextended, newworkers0/main sends0. Broad computer-control goal remains active.
Draft content review, two fixed-epoch genuine nonauthor approvals, actual-current
nonauthor combination and live authority/CAS reconciliation remain separate.

Publication first diff-check reports4775 trailing-CR errors on unchanged Windows
CRLF images; complete2075774-byte stdout is retained losslessly as gzip. First
build also stops while printing that saved diagnostic through CP932. No commit
exists from that attempt. A separate archive-only v2 recognizes CR-at-EOL and
preserves all bytes using this package-local .gitattributes; scientific inputs,
source, results and first errors are unchanged. See PUBLICATION_FIRST_FAILURE.

Second archive attempt retains the same CR warnings: revision-to-revision diff
in unchanged delivery checkout did not load proposed package attributes. Literal
CRLF bytes and cached attributes are confirmed in CRLF_DIFF_DIAGNOSIS. Separate
v3 checks the candidate-owned index using --cached; no source or raw replay.
Full second stdout is retained losslessly; final package/check counts are
specified by the fixed PR descriptor, not historical first attempt counts.
