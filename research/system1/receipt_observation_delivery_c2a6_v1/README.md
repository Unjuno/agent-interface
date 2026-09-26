# Caller-observed receipt timing: retained r9k4 evidence

Issue #4390; successor to #4231. This directory publishes the completed
`receipt-boundary-r9k4-20260925` **LOCAL_PILOT** retrospectively. No original
experiment is restarted and this publication is not public preregistration.

## Measurement correction

#4231 owner.py samples `receipt_ns` before sending. Its caller has no recorded
read-return timestamp. Earlier prose calling approximately171 ms caller arrival
was too strong. The unchanged original sources remain at their historical path;
Issue #4231 now carries correction comment5841110841.

The later r9k4 study separately records effect completion, sender sample,
caller read return, report decision and owner exit. Under its single terminal
newline-frame protocol, waiting for producer EOF adds irrelevant lifetime delay.
This is a result-availability boundary, not a general replacement for EOF.

## Retained results

42 sessions /84 real owner-caller processes;7 conditions x2 readers x3 repetitions.
All three pilot batches were consumed once after a local18-file freeze. Fourteen
construction cases are excluded. The raw-only audit has3141 checks/errors0;
15 effective, rehashed copied-evidence controls reject;11 pure unit methods pass.

| Condition | EOF-read median ms | Frame-read median ms | Effect |
|---|---:|---:|---|
| FAST |80.183|60.343|ON_TIME|
| READER_DELAY |180.178|180.181|ON_TIME|
| EMIT_DELAY |180.196|160.443|ON_TIME|
| LATE_COMMIT |190.299|170.474|LATE|
| OPEN_STREAM |240.250|60.370|ON_TIME|
| NO_COMMIT |80.211|60.359|NO_EFFECT|
| TRUNCATED |80.180|80.175|UNKNOWN|

Deadline120 ms; supplied Linux x86_64/CPython3.13.5, shared Xeon Platinum8573C,
CPU/frequency not pinned,3 observations per cell. Directed delays, not production
latency distributions. Sender proxy falsely certifies9 late observations as
on-time and mislabels6 on-time effects as late. Frame reading does not remove
reader scheduling delay. UNKNOWN never means no effect or permission to retry.

## Complete bytes and read-only reproduction

`MANIFEST.json` binds21 binary segments of one90,680-byte XZ archive containing
**all972 original files /836,208 member bytes**. No nested predecessor archive
is omitted. Three readable original source copies are checked against the archive.
All remaining source, full PLAN/proof/variable table, REPORT, raw case bytes,
original audit/controls,18-file freeze, construction and publication history
are restored verbatim. Historical README/publication flags remain historical;
they are not silently rewritten as if publication preceded the experiment.

```sh
python -S -B verify.py
python -S -B -m unittest -v test_restore
# Optional: inspect originals without running anything
python -S -B restore.py /tmp/r9k4-new-destination
```

The verifier runs only the original read-only audit/controls and pure units.
It never starts source/execute.py, source/supervise.py, caller, owner or any
predecessor runner. Use a new destination with a trusted/quiescent parent;
the restorer is not an adversarial filesystem sandbox.

## H / T / D / C / U and integration boundary

H: sender time cannot certify caller observation; a complete terminal frame
can be available before producer exit. T: original42-session private process
experiment, now byte-only reconstruction. D: retain
PASS_LOCAL_RECEIPT_OBSERVATION_BOUNDARY; publication qualifies only after complete
Git-object readback and unchanged reconstruction, not from summary text.
C: cooperative same-clock single-terminal-frame owner/journal; caller read return
is not kernel arrival or model consumption. Fsync return is a fixture completion
marker, not power-loss durability. U: arbitrary framing, authentic receipts,
distributed clocks, model/task usefulness, token/latency benefit and production
transport adoption remain untested. Same-author separate audit is not external
human review. No calibrated timing uncertainty is invented.

Concrete #2789 decision: preserve distinct effect and observation timestamps;
never use a delayed/missing receipt to authorize blind replay. This is research
evidence, not runtime/default promotion or completion of the global ROADMAP.
