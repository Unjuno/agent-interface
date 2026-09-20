# NativeHandleBridge XID-reuse experiment — STOP

Issue: #3464 (successor to #3419)

## H/T/D/C/U

- **H:** An old visual alias might remain eligible if an XID is reused by a visually identical replacement process.
- **T:** One isolated Obstac/OrbStack run; networking disabled; source `f33695096b7460dc148d348d6c9a26c7815c1569`; image `agent-interface-2558-orbstack:20260920`, digest `sha256:1a16aa431254514de58c909e84e5094a8e894caac11bf4c9d937dde6ea6d6398` (linux/arm64).
- **D:** Raw runner JSONL is `raw.jsonl`, SHA-256 `5a841e3395ee40bd2a73fc24e9d10ef5033b825e66724c54c62dea5de47582c6` (3 complete rows). It records p1 PID 14, XID 4194318, focus/surface 4194318, geometry 80,80,360,200; exact target patch SHA-256 `700f2b981adf4167449d3eb71eb0b57c841939b11731c660112ee39b8bd08d44`; p1 exited -15. The run then raised Xlib `BadDrawable` while querying geometry through the bridge's still-registered resource. No old-alias attempt or positive control occurred. Two earlier setup failures are retained locally, not counted as allocations or semantic evidence.
- **C:** **STOP / INVALID ALLOCATION.** The experiment did not establish p2 XID, XID reuse, bridge admission, emissions, or replacement effect. This is a harness/bridge-lifecycle failure, not a pass or stale-handle counterexample.
- **U:** No conclusions about XID reuse or target safety. Do not promote the bridge or change #3419 based on this run.

## Follow-up gate

Any successor must first implement a read-only, independently auditable replacement-window discovery and explicit bridge rebinding protocol, then pre-register a new allocation. Do not rerun or reinterpret this allocation. Preserve this record as-is.