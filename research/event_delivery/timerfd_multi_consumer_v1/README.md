# Retained timerfd multi-consumer ownership experiment — Issue #4056

This is retrospective delivery of `timerfd-multi-consumer-20260922-01`,
not a new formal allocation and not GitHub preregistration. The original local
freeze preceded measurement; the Issue and this publication branch came later.
Original RESULT.md, PLAN.md, source, raw data and historical LOCAL_ONLY messages
are unchanged. This dated delivery note supersedes only their publication state.

## Result and integration boundary

PASS_TIMERFD_OWNERSHIP_BOUNDARY_SCOPED: 20 fresh cases, 40 actors,
two predeclared batches, no retry/replacement/tuning. Giving separate workers
aliases of one timerfd does not grant independent consumption or rearm/disarm
state. Closing one alias does not cancel the timer for surviving aliases.
Independent timer objects isolate state; neither mode proves broadcast delivery.
Do not convert readiness or expiration count into model acknowledgement,
application observation or action authority. No production runtime was changed.

This is the multiple-reader/descriptor boundary excluded by #4001.
It does not rerun #3986/#4031/#4044 or the original #4001 allocation.

## Lossless evidence and read-only verification

PACK.json binds 14 binary parts to one XZ-compressed UTF-8 file map.
Unpacking restores all 289 original files / 1,156,979 bytes, including every
construction/formal IPC frame, kernel fdinfo, observed exit and old publication
limitation. Original ZIP container bytes are identified but not reconstructed;
all original member bytes are reconstructed. Hashes provide integrity, not
authentication. Use trusted source/output parents with no concurrent mutation.

From this directory, use a fresh destination:

```sh
python -S -B unpack.py /tmp/timerfd-4056-review
cd /tmp/timerfd-4056-review
sha256sum -c SHA256SUMS
python -S -B audit_all.py . > /tmp/timerfd-4056-audit.json
cmp AUDIT.json /tmp/timerfd-4056-audit.json
python -S -B test_audit.py
```

The unpacker only restores data. The audit imports the separate audit module,
not actor.py/run.py, and does not arm a timer. Do not rerun consumed batches.
The directly readable actor is the exact original; its expected peer/source
files are in the restored tree.

## Validation and limits

Continuation verified all 288 original checksum entries, unchanged audit output
SHA256 c527362686d2fc2dc11dfffb90934dabda775faac3ecdf9007937f834c8ae5b1,
4,086 raw checks, all 12 semantic mutations in each batch and six unit methods.
All 13 original frozen files remain unchanged. Separate implementation/process
by the same author is not independent human review. Validation details are
retained in PUBLICATION_VALIDATION.json; current-head CI/review are separate gates.

Original execution: provided Linux x86_64/CPython 3.13.5/glibc 2.41,
CLOCK_MONOTONIC, little-endian uint64 ABI, AMD EPYC 9V74 guest, uncontrolled
frequency/load. No Docker/OrbStack image-attested replication, model/provider,
GUI/input, runtime promotion, speed/token benefit, power-loss/suspend/restart,
natural failure-rate estimate or global-roadmap completion is claimed.
