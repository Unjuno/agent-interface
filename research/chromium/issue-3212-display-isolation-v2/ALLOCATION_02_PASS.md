# #3419 allocation 2 — combined generation/input acceptance

Decision: PASS_COMBINED_GENERATION_INPUT_SCOPED

## H/T/D/C/U

- H: A p1→p2 generation transition with a p2/decoy pair rejects stale p1 authority, prevents decoy input from mutating p2, and admits exact p2 input/effect.
- T: Fresh Debian bookworm-slim Chromium/Xvfb/Openbox allocation. p1 on :290/CDP 9401 was terminated; p2 and decoy ran on :291/CDP 9402/9403. Old p1 target was attempted; decoy then p2 received x; titles were independently read.
- D: Four raw JSONL rows, raw SHA-256, manifest decision and independent recomputation are retained below. No production code changed.
- C: PASS requires old target rejection, decoy-only effect, exact p2 effect, raw row count/hash and independent audit match.
- U: One fresh allocation and one Chromium fixture; no cross-application reliability, human tempo, product readiness or general GUI claim.

## Obstac result

OBSTAC_3419_ALLOCATION_02 {"audit_recomputed":true,"decision":"PASS_COMBINED_GENERATION_INPUT_SCOPED","raw_jsonl_sha256":"57233e2a13c34c26da7e2176aef55898a0dc66ac80ff1e54e3b529ad3b351f79","rows":4}

- old target: rejected
- decoy input receipt: decoy_title=os-input-decoy; p2_title_after_decoy=p2-ready
- p2 input receipt: p2_title=os-input-p2
- XID observations: p1=4194307; p2=4194307; decoy=6291459
- independent audit: true

## Raw JSONL

~~~jsonl
{"event":"old_target","value":"rejected"}
{"decoy_title":"os-input-decoy","event":"decoy_input_effect","p2_title_after_decoy":"p2-ready","xid":"6291459"}
{"event":"p2_input_effect","p2_title":"os-input-p2","xid":"4194307"}
{"event":"p1_xid","xid":"4194307"}
~~~

Manifest: rows=4; raw_jsonl_sha256=57233e2a13c34c26da7e2176aef55898a0dc66ac80ff1e54e3b529ad3b351f79; audit_recomputed=true.

## Scope

This is a scoped acceptance of the pinned Chromium/Xvfb multi-window path. It does not establish multi-application reliability or close #3266. Allocation 1 remains immutable as HOLD_RAW_MANIFEST_MISSING.
