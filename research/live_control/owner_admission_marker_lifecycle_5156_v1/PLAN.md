# Owner admission marker lifecycle boundary probe

## H/T/D/C/U

- **H:** after each admitted key is released by asynchronous cancellation,
  the next admission observes the verified cleanup record and prunes the old
  marker; repeated cycles therefore keep wrapper marker count bounded.
- **T:** run 64 cancel/owner-cleanup/re-admission cycles against the actual
  `input_owner_v10` owner thread with deterministic fake Xlib/XTest; inspect
  marker count after every new admission.
- **D:** PASS only if each owner cleanup is verified and the wrapper retains
  exactly one marker for the newest admission at every cycle (maximum count
  one), while preserving one cleanup KeyRelease per admitted KeyPress.
- **C:** exact PR #7376 head `0f112dcae1e3b108ae2eecddebd95b829b8fbffa`,
  wrapper SHA256 `672e7471b91f321f0d8723ef6277d974b24b2fa322f5e89907b17bf92998f177`,
  owner SHA256 `ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b`.
- **U:** fake Xlib exercises the actual Python owner queue and cleanup loop,
  but not an X server, physical input, normal application workload, memory
  bytes, or production session frequency. The final async cleanup remains
  represented by one cached marker until the next wrapper operation or close.

## Result

The probe passed all 64 cycles. Every iteration observed a verified cancelled
owner release and retained one marker for the newly admitted lease; maximum
marker count was one. No physical X11 or GUI was used.
