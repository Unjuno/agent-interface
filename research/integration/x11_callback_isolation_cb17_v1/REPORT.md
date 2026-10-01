# X11 callback exception isolation — Issue #4308

**PASS_X11_CALLBACK_FAILURE_ISOLATION_SCOPED**. This is bounded observation-delivery evidence, not a production/runtime/task claim.

## First outcome

Four immutable ten-case batches completed once after public source/gate freeze. Forty fresh private Xvfb lifetimes, 120 real PropertyNotify events, 120 producer/observer/server exits0 and four observed batch exits0. Same-batch reruns, replacement, exclusion and post-result tuning: all0.

| Per-policy endpoint | EVENT_CATCH | SUBSCRIBER_CATCH |
|---|---:|---:|
| Cases |20|20|
| Requested subscriber deliveries |120|120|
| ACKs |104|112|
| Healthy-subscriber missing delivery |8|0|
| Failing callback without ACK |8|8|
| ACK followed by exception |8|8|

All NONE positives delivered six ACKs per case. Both subscribers received event3 in every case. No callback retry or duplicate ACK occurred. An AFTER_ACK exception is retained as acknowledged-but-error, not normal return. The failing subscriber is not repaired by isolating its exception.

Frozen separate raw-only audit: **2598 checks, errors=[]**. Frozen corruption gate: **12/12 actual changed payloads rejected**, no no-ops or parser-fallback errors. Source, native event bytes/window/atom/property, callback journals, wire ordering, actual process exits and private-display cleanup reconcile.

## H / T / D / C / U

H: catching a declared callback exception around the whole subscriber loop skips later healthy callbacks for that event; per-subscriber catching confines that interruption while preserving failure accounting.

T: two policies, five conditions (NONE; first/last callback failing before/after ACK on event2), AB/BA callback orders, two repetitions. Three real property notifications per case; independent producer and dispatcher processes. Provided Linux x86_64 container, CPython3.13.5, Xlib module version0.15, authenticated TCP-disabled Xvfb. No keyboard/mouse/XTEST, model/provider, host desktop, user data or experiment network. No Docker/OrbStack image-attestation claim.

D: exact40-case/process/raw coverage, zero healthy loss in candidate, all expected control counts, independent audit and all12 effective mutations are required jointly. Missing evidence or ineffective controls would be HOLD/STOP, not a waived gate.

C: this is an authored synchronous RuntimeError failure in a cooperative single-threaded dispatcher. The deliberately weak comparator is not alleged production behavior. Python exception propagation is known; the measured residual is native-event/dispatcher/acknowledgement composition.

U: callback hangs, logger failure, shared-state corruption, process death, reentry, dynamic subscriptions, hostile subscribers, distributed exactly-once, natural failure probability and model/task/token/latency benefit remain untested. Time readings are diagnostic, not a calibrated benchmark. Same-author independent implementation/process is not independent human review.

## Preserved construction failures

The first excluded observer failed while converting Python-Xlib's string property value to bytes. Exact Latin-1 normalization was added before freeze; original source and stderr remain. The first audit rehearsal rejected missing/duplicate wire records through a malformed parser fallback; before freeze the auditor gained an immediate wire-count return. The original rehearsal and corrected12/12 rehearsal remain. Seven final audit tests passed before freeze. No scientific result was used to tune these changes.

## Source-first provenance and reproduction

Source freeze commit: `296e360be0b2f8306a2cb2e3aa91f3fe6808d3df`.
FREEZE SHA256: `8fc7183ad4819acfe8f5625f7b9e0aaff15f929456b9db99b7b0659dd0c31a7d`.
Source archive SHA256: `e89911bbdb21d4d6f92c207b95466842439bb292e61d315cd35a79d32e8c91f2`.
All six source transport/manifest/restorer Git blobs were read back with exact local identity before formal invocation. The complete evidence capsule retains source, excluded construction, all40 raw cases, callback journals, process/launcher records, first audit and all12 mutation payloads.

Read only, from this publication directory:
```
python -B unpack.py EVIDENCE_MANIFEST.json /tmp/cb17-review-new
python -B /tmp/cb17-review-new/source/audit.py /tmp/cb17-review-new > /tmp/cb17-audit.json
cmp /tmp/cb17-review-new/AUDIT.json /tmp/cb17-audit.json
```
Do not rerun the consumed native-event batches. The restorer verifies digests, bounds expansion and writes only relative regular files into a new directory. It does not execute source.

## Integration constraint

Native dequeue, subscriber attempt, subscriber ACK, callback normal return and callback exception are distinct evidence. Isolation can preserve the healthy subscriber without making the failed subscriber successful. This adds no shared runtime/default and does not complete the repository ROADMAP. Predecessor #4085/#4008 and all prior results remain unchanged.
